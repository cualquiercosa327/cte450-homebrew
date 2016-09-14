#!/usr/bin/env node

const HID = require('node-hid');
const readline = require('readline');
const fs = require('fs');
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

var iir = [0];

function do_sample(adcr) {
    const c = 0.2;
    var s = iir[0] = iir[0] * 0.2 + adcr * (1.0 - c);
    var ticks = '#'.repeat(Math.max(0, Math.min(1000, Math.round(s) - 550)));
    console.log(s, ticks);
}

dev.on('data', (data) => {
    if (data.length >= 5) {
        do_sample(data.readUInt16LE(2) >> 4);
        do_sample(data.readUInt16LE(4) >> 4);
    }
});
