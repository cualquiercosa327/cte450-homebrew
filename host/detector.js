#!/usr/bin/env node

const readline = require('readline');
const Fili = require('fili');
const CircularBuffer = require('circular-buffer');
const stats = require('stats-lite');

var iirCalculator = new Fili.CalcCascades();

var highpass = new Fili.IirFilter(iirCalculator.highpass({
    order: 2,
    characteristic: 'bessel',
    Fs: 128,
    Fc: 0.1
}));

var lowpass = new Fili.IirFilter(iirCalculator.lowpass({
    order: 2,
    characteristic: 'bessel',
    Fs: 128,
    Fc: 12
}));

var pulse_width_filter = [];
var pulse_thresholds = [];
for (var i = 0; i < 2; i++) {
    pulse_width_filter[i] = new Fili.IirFilter(iirCalculator.lowpass({
        order: 2,
        characteristic: 'bessel',
        Fs: 128,
        Fc: 0.5
    }));
}

function decode_em(bits) {
    // Test signal, repeating 32-bit manchester code
    // decode_em('1111111110001101111000000000001111111011001001001100011111001010') == '17007e948f'
    // decode_em('1111111110011001100000000000001111011110101000101101111000100010') == '36007752b8'
    // 0101010101010101011010010110100101101010101010101010101010100101010110010101011001100110101001100101100101010110101001101010011001010101010101010110100101101001011010101010101010101010101001010101100101010110011001101010011001011001010101101010011010100110

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
    result = result.join('');

    // Also show latter portion in decimal, to make codes easier to recognize
    result = result + '-' + parseInt(result.substr(2), 16);

    return result;
}

var bits = '0'.repeat(128);
var pulse_state = 0;
var pulse_timer = 0;

var threshold = 0;
var manchester = '';
var decoded = null;

const rl = readline.createInterface({input: process.stdin});
rl.on('line', (input) => {
    var y = parseInt(input);

    y = Math.pow(y, 0.007) * 1e6;       // Try to correct for extreme nonlinearity
    y = highpass.singleStep(y);         // Take out DC bias without distorting shape too much
    y = lowpass.singleStep(y);          // Filter out HF noise, get a nice pulse shape
    var y_state = 0|(y > 0);            // Binary threshold

    var bit = null;

    if (y_state == pulse_state) {
        pulse_timer++;
    } else {
        // Zero crossing. Keep pulse width statistics

        threshold = pulse_thresholds[pulse_state];
        var next_threshold = pulse_timer * 1.5;

        if (pulse_timer < threshold) {
            // Single bit
            bit = '' + pulse_state;
        } else {
            // Double bit
            bit = '' + pulse_state + pulse_state;
            next_threshold /= 2;
        }

        pulse_thresholds[pulse_state] = pulse_width_filter[pulse_state].singleStep(pulse_timer);

        pulse_state = y_state;
        pulse_timer = 0;
    }

    if (bit !== null) {
        bits = bits + bit;
        bits = bits.substr(bits.length - 128);

        // Try every rotation of the buffer
        const doubled = bits + bits;
        for (var i = 0; i < 128; i++) {
            manchester = doubled.substr(i, 128).replace(/.(.)/g, '$1');
            decoded = decode_em(manchester) || decoded;
        }
    }

    console.log(bits, decoded, y, pulse_timer, threshold, bit || '.');
});

