#!/usr/bin/env node

const HID = require('node-hid');
const readline = require('readline');
const rl = readline.createInterface({input: process.stdin});
const dev = new HID.HID(0x56a, 0x17)

var sample_spacing = 7;
var pattern_length = 128;
var smoothing = 0.8;

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


dev.on('data', (data) => {
	var adcr = data.readUInt16LE(3) >> 4;
	var counter = data.readUInt16LE(1);
	var bin = (counter * sample_spacing) % pattern_length;

	bins[bin] = adcr * (1.0 - smoothing) + (bins[bin] || 0) * smoothing;

	var min = Math.min.apply(null, bins);
	var max = Math.max.apply(null, bins);
	var middle = (max + min) / 2;

	function printer(bin) {
		if (max - min > 10) {
			return (bin >= middle) ? "#" : ".";
		} else {
			return "-";
		}
	}

	var summary = bins.map(printer).join('');

	console.log(summary, Math.round(min), Math.round(max), counter);
});
