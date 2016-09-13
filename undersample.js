#!/usr/bin/env node

const HID = require('node-hid');
const readline = require('readline');
const fs = require('fs');
const rl = readline.createInterface({input: process.stdin});
const dev = new HID.HID(0x56a, 0x17)

var sample_spacing = 15;
var pattern_length = 256;
var smoothing = 0.99;

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

dev.on('data', (data) => {
	if (data.length == 5) {
		var adcr = data.readUInt16LE(3) >> 4;
		var counter = data.readUInt16LE(1);
		var bin = (counter * sample_spacing) % pattern_length;

		bins[bin] = adcr * (1.0 - smoothing) + (bins[bin] || 0) * smoothing;

		var min = Math.min.apply(null, bins);
		var max = Math.max.apply(null, bins);
		var middle = median(bins)
		var stats = '[' + Math.round(min) + ',' + Math.round(middle) + ',' + Math.round(max) + ']';

		function printer(bin) {
			return (bin >= middle) ? '#' : '.';
		}

		var summary = bins.map(printer).join('');

		console.log(summary, stats, counter, adcr);

		if ((counter & 0xff) == 0) {
			fs.writeFileSync('bins.csv', bins.join('\n'));
		}
	}
});
