#!/usr/bin/env node

const HID = require('node-hid');
const readline = require('readline');
const rl = readline.createInterface({input: process.stdin});
const dev = new HID.HID(0x56a, 0x17)
var error_limit = 100;

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

dev.on('data', (data) => {
	console.log(data.toString('hex'));
});

dev.on('error', (e) => {
	console.log('err: ' + e);
	if (error_limit-- > 0) {
		setTimeout(() => {
			dev.resume();
		}, 10);
	}
});
