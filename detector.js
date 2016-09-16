#!/usr/bin/env node

const readline = require('readline');
const Fili = require('fili');
const CircularBuffer = require('circular-buffer');

var iirCalculator = new Fili.CalcCascades();

var highpass = new Fili.IirFilter(iirCalculator.highpass({
    order: 3,
    characteristic: 'butterworth',
    Fs: 922,
    Fc: 0.2
}));

var lowpass = new Fili.IirFilter(iirCalculator.lowpass({
    order: 5,
    characteristic: 'butterworth',
    Fs: 922,
    Fc: 70
}));


const history = new CircularBuffer(4096);

const rl = readline.createInterface({input: process.stdin});
rl.on('line', (input) => {
    var y = parseInt(input);

    y = highpass.singleStep(y);
    y = lowpass.singleStep(y);

    history.enq(y);

    var decoded = null;
    // for (var bit_period = 8; bit_period < 10; bit_period += 1/128.0) {
    //     decoded = decoded || try_decode(bit_period);
    // }

    console.log(y, decoded);
});

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
    return decode_em(bits);
}
