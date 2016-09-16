#!/usr/bin/env node

// Poke code into RAM, read back ADC values.

const HID = require('node-hid');
const readline = require('readline');
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

dev.on('data', (data) => {
    if (data.length == 9) {
        for (var i = 0; i < 4; i++) {
            console.log(data.readUInt16LE(1 + i*2));
        }
    }
});
