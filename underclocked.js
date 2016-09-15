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

const firCalculator = new Fili.FirCoeffs();
const firBandpass = new Fili.FirFilter(firCalculator.bandpass({
    order: 128,
    Fs: 922,
    F1: 70,
    F2: 250,
}));

const clkgain = 1e-5;
var clkrate = 1/9.0;
var clk = 0;

function do_sample(adcr) {

    // Input bandpass filter
    const y = firBandpass.singleStep(adcr);

    // Clock recovery PLL
    clk = (clk + clkrate) % 1.0;
    var phaseErr = (y > 0) ^ (clk > 0.5);
    clkrate = Math.max(0.05, Math.min(0.4, clkrate + phaseErr * clkgain));

    const width = 200;
    const middle = width/2;
    const gain = 4.0;
    const w = Math.max(0, Math.min(middle, Math.abs(Math.round(y * gain))));
    var ticks = y > 0 ? (' '.repeat(middle) + '1'.repeat(w)) :
                        (' '.repeat(middle-w) + '0'.repeat(w));

    console.log(y);
    // console.log(ticks);
    // console.log(0|(y>0), 0|(clk>0.5), phaseErr, clk, clkrate, ticks);
}

dev.on('data', (data) => {
    if (data.length == 9) {
        do_sample(data.readUInt16LE(1) >> 4);
        do_sample(data.readUInt16LE(3) >> 4);
        do_sample(data.readUInt16LE(5) >> 4);
        do_sample(data.readUInt16LE(7) >> 4);
    }
});
