#!/usr/bin/env node

const HID = require('node-hid');
const readline = require('readline');
const fs = require('fs');
const Fili = require('fili');
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

var firCalculator = new Fili.FirCoeffs();
var firBandpass = new Fili.FirFilter(firCalculator.bandpass({
    order: 128,
    Fs: 630,
    F1: 40,
    F2: 100,
}));

function do_sample(adcr) {
    const y = firBandpass.singleStep(adcr);
    const width = 200;
    const middle = width/2;
    const gain = 4.0;
    const w = Math.max(0, Math.min(middle, Math.abs(Math.round(y * gain))));
    var ticks = y > 0 ? (' '.repeat(middle) + '1'.repeat(w)) :
                        (' '.repeat(middle-w) + '0'.repeat(w));
    console.log(ticks);
}

dev.on('data', (data) => {
    if (data.length >= 5) {
        do_sample(data.readUInt16LE(2) >> 4);
        do_sample(data.readUInt16LE(4) >> 4);
    }
});
