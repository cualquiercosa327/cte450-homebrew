#!/usr/bin/env node

const HID = require('node-hid');
const readline = require('readline');
const fs = require('fs');
const rl = readline.createInterface({input: process.stdin});
const dev = new HID.HID(0x56a, 0x17)

var sample_spacing = 3
var pattern_length = 64;
var smoothing = 0.0;

var bins = [];

rl.on('line', (input) => {
    const tokens = input.split(' ');
    const addr = parseInt(tokens[0], 16);
    const data = [0x11];
    for (var i = 1; i <= 16; i++) {
        data[i] = i < tokens.length ? parseInt(tokens[i], 16) : 0;
    }
    dev.sendFeatureReport([0x10, addr >> 8, addr & 0xff]);
    dev.sendFeatureReport(data);
});

function median(values) {
    values = values.slice(0);
    values.sort( function(a,b) {return a - b;} );
    var half = Math.floor(values.length/2);
    if (values.length % 2) {
        return values[half];
    } else {
        return (values[half-1] + values[half]) / 2.0;
    }
}

function decode_em(bits) {
    // Test signal, repeating 32-bit manchester code
    // 17007E948F
    //
    //   01 01 01 01 01 01 01 01 01
    //               10 10 10 01 01
    //               10 01 01 01 01
    //               10 10 10 10 10
    //               10 10 10 10 10
    //               10 01 01 01 01
    //               01 01 01 10 01
    //               01 10 10 01 10
    //               10 01 10 10 01
    //               01 10 10 10 01
    //               01 01 01 01 10
    //               10 01 10 01 10

    // Header
    for (var i = 0; i < 9; i++) {
        if (!bits[i]) return;
    }

    // Stop bit
    if (bits[63]) return;

    // Row parity
    for (var row = 0; row < 10; row++) {
        var p = 0;
        for (var i = 0; i < 5; i++) {
            p ^= bits[9 + row*5 + i];
        }
        if (p) return;
    }

    // Column parity
    for (var col = 0; col < 4; col++) {
        var p = 0;
        for (var i = 0; i < 11; i++) {
            p ^= bits[9 + i*5 + col];
        }
        if (p) return;
    }

    // Hex digits
    var result = [];
    for (var row = 0; row < 10; row++) {
        var nyb = (bits[9 + row*5 + 0] ? 8 : 0) +
                  (bits[9 + row*5 + 1] ? 4 : 0) +
                  (bits[9 + row*5 + 2] ? 2 : 0) +
                  (bits[9 + row*5 + 3] ? 1 : 0) ;
        result.push(nyb.toString(16));
    }
    return result.join('');
}


function shift_decode(bits) {
    var doubled = bits.concat(bits);
    for (var offset = 0; offset < bits.length; offset++) {
        var r = decode_em(doubled);
        if (r) return r;
        var r = decode_em(doubled.map((n) => !n));
        if (r) return r;
        doubled.shift();
    }
}


dev.on('data', (data) => {
    if (data.length == 5) {
        var adcr = data.readUInt16LE(3) >> 4;
        var counter = data.readUInt16LE(1);
        var bin = (counter * sample_spacing) % pattern_length;
        bins[bin] = adcr * (1.0 - smoothing) + 0;//(bins[bin] || 0) * smoothing;

        var min = Math.min.apply(null, bins);
        var max = Math.max.apply(null, bins);
        var middle = median(bins)
        var stats = '[' + Math.round(min) + ',' + Math.round(middle) + ',' + Math.round(max) + ']';

        var bits = bins.map( (bin) => (bin >= middle ? 1 : 0) );
        var summary = bits.join('');

        console.log(summary, stats, counter, adcr, shift_decode(bits) || '');

        if ((counter & 0xff) == 0) {
            fs.writeFileSync('bins.csv', bins.join('\n'));
        }
    }
});
