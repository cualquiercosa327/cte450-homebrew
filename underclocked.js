#!/usr/bin/env node

const HID = require('node-hid');
const readline = require('readline');
const fs = require('fs');
const Fili = require('fili');
const CircularBuffer = require('circular-buffer');

const rl = readline.createInterface({input: process.stdin});
const dev = new HID.HID(0x56a, 0x17)

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

const firCalculator = new Fili.FirCoeffs();
const firBandpass = new Fili.FirFilter(firCalculator.bandpass({
    order: 32,
    Fs: 922,
    F1: 10,
    F2: 190,
}));

const history = new CircularBuffer(512);

function do_sample(adcr) {
    // history.enq(firBandpass.singleStep(adcr));

    console.log(adcr);

    // var decoded = null;
    // for (var bit_period = 0.9; bit_period < 1.2; bit_period += 0.01) {
    //     decoded = decoded || try_decode(bit_period);
    // }

    // console.log(history.get(0), decoded);
}

function decode_em(bits) {
    // Test signal, repeating 32-bit manchester code
    // decode_em('1111111110001101111000000000001111111011001001001100011111001010') == '17007e948f'
    // decode_em('1111111110011001100000000000001111011110101000101101111000100010') == '36007752b8'

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

function try_decode(bit_period) {
    const bits = []
    if (history.size() < bit_period * 130) {
        return;
    }
    for (var i = 0; i < 64; i++) {
        const sample1 = history.get(Math.round(bit_period * (i * 2 + 0)));
        const sample2 = history.get(Math.round(bit_period * (i * 2 + 1)));
        bits[i] = 0|(sample2 > sample1);
    }
    // console.log(bits.join(''));
    return bits[0];
    // return decode_em(bits);
}

dev.on('data', (data) => {
    if (data.length == 9) {
        do_sample(data.readUInt16LE(1) >> 4);
        do_sample(data.readUInt16LE(3) >> 4);
        do_sample(data.readUInt16LE(5) >> 4);
        do_sample(data.readUInt16LE(7) >> 4);
    }
});
