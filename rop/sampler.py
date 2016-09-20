#!/usr/bin/env python

from roplib import *

def setup_func():
    r = Ropper()

    r.le16(adc_shutdown)
    r.irq_global_disable()

    # Usually the tablet uses a 750 kHz carrier, but we can reprogram it.
    r.set_wclk_freq(125000)

    # Normally these timers control the scanning cycle, but we're using timed delays below instead
    r.poke(reg_wsnd, 20)                # Transmit length
    r.poke(reg_wrcv, 120)               # Receive length
    r.poke(reg_wwai, 120)               # Repeat delay / ADC conversion time

    r.pokew(reg_wsadr, adr_y[0])        # Where to transmit (Y00 has the lowest loss and is on the front side)
    r.memcpy(reg_wradr, reg_wsadr, 2)   # Receive at the same spot

    # Longest ADC conversion time (1/128)
    r.poke(reg_admrc, 0x03)
    r.poke(reg_adrlc, 0x01)

    # Pre-load packet header
    r.poke(ep1_buffer + 0, 2)
    r.poke(reg_ep1cnt, 9)

    return r

def loop_func(precopy):
    r = Ropper()

    for bit in range(4):

        r.poke(reg_wcdly1, 0x06)   # Reset delay timers
        r.poke(reg_wcon, 0xd0)     # Begin timed transmit cycle
        r.delay(0.15)

        r.adc_start()              # Timed ADC cycle
        r.delay(0.6)
        r.memcpy(factory_temp_ram + bit*2, reg_adrlc, 2)

        r.poke(reg_wcon, 0xb0)     # Turn the charge pump back on

        precopy(r)

    # Send USB packet (buffered in temp ram)
    r.memcpy(ep1_buffer + 1, factory_temp_ram, 8)
    r.le16(ep1sta_bit3_set)

    return r

if __name__ == '__main__':
    write_loop(setup_func(), loop_func)
