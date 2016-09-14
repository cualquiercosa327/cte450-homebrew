#!/usr/bin/env node

const HID = require('node-hid');
const readline = require('readline');
const fs = require('fs');
const rl = readline.createInterface({input: process.stdin});
const dev = new HID.HID(0x56a, 0x17)

var sample_spacing = 9;
var pattern_length = 128;
var fir_depth = 1;

// Empty FIR filter for each bin where we recover half-bits
var bins = [];
var bin_averages = [];
for (var bin = 0; bin < pattern_length; bin++) {
    bins.push([]);
    bin_averages.push(0.0);
}

rl.on('line', (input) => {
    // Write device memory

    const tokens = input.split(' ');
    const addr = parseInt(tokens[0], 16);
    const data = [0x11];
    for (var i = 1; i <= 16; i++) {
        data[i] = i < tokens.length ? parseInt(tokens[i], 16) : 0;
    }
    // Set write address
    dev.sendFeatureReport([0x10, addr >> 8, addr & 0xff]);
    // Write exactly 16 bytes
    dev.sendFeatureReport(data);
});

function decode_em(bits) {
    // Test signal, repeating 32-bit manchester code
    // decode_em('1111111110001101111000000000001111111011001001001100011111001010') == '17007e948f'
    // decode_em('1111111110011001100000000000001111011110101000101101111000100010') == '36007752b8'

    // Manchester encoded 36007752b8:
    // 01010101010101010110100101101001011010101010101010101010101001010101100101010110011001101010011001011001010101101010011010100110

    // Header
    for (var i = 0; i < 9; i++) {
        if (!(0|bits[i])) return;
    }

    // Stop bit
    if (0|(bits[63])) return;

    // Row parity
    for (var row = 0; row < 10; row++) {
        var p = 0;
        for (var i = 0; i < 5; i++) {
            p ^= 0|(bits[9 + row*5 + i]);
        }
        if (p) return;
    }

    // Column parity
    for (var col = 0; col < 4; col++) {
        var p = 0;
        for (var i = 0; i < 11; i++) {
            p ^= 0|(bits[9 + i*5 + col]);
        }
        if (p) return;
    }

    // Hex digits
    var result = [];
    for (var row = 0; row < 10; row++) {
        var nyb = (0|(bits[9 + row*5 + 0]) ? 8 : 0) +
                  (0|(bits[9 + row*5 + 1]) ? 4 : 0) +
                  (0|(bits[9 + row*5 + 2]) ? 2 : 0) +
                  (0|(bits[9 + row*5 + 3]) ? 1 : 0) ;
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
    if (data.length >= 5) {
        var adcr = data.readUInt16LE(3) >> 4;
        var counter = data.readUInt16LE(1);

        // Current bin in the undersampled waveform
        var bin_id = (counter * sample_spacing) % pattern_length;
        var bin = bins[bin_id];

        // Update simple FIR filter
        bin.push(adcr);
        if (bin.length > fir_depth) bin.shift();
        bin_averages[bin_id] = bin.reduce((a,b) => a+b) / bin.length;

        // Find manchester-encoded bits
        var bits = [];
        for (var i = 0; i < pattern_length/2; i++) {
            var dif = bin_averages[i*2+1] - bin_averages[i*2+0];
            bits[i] = dif >  2 ? '1' :
                      dif < -2 ? '0' : 'x';
        }
        var summary = bits.join('');

        console.log(summary, bin.length, counter, adcr, '\t\t', shift_decode(bits) || '-');

        if ((counter & 0xff) == 0) {
            fs.writeFileSync('bins.csv', bin_averages.join('\n'));
        }
    }
});
