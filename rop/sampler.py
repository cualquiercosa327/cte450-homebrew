#!/usr/bin/env python

from roplib import *

def setup_func():
    r = Ropper()

    r.irq_global_disable()

    # Set up FEB0h peripheral: Enabled, wait enabled, charge pump on
    r.poke(reg_wcon, 0xb0)

    # Usually the tablet uses a 750 kHz carrier, but we can reprogram it.
    r.set_wclk_freq(125000)

    # Normally these timers control the scanning cycle, but we're using timed delays below instead
    r.poke(reg_wsnd, 255)               # Transmit length
    r.poke(reg_wrcv, 127)               # Receive length
    r.poke(reg_wwai, 127)               # Repeat delay / ADC conversion time

    r.pokew(reg_wsadr, adr_y[0])        # Where to transmit (Y00 has the lowest loss and is on the front side)
    r.memcpy(reg_wradr, reg_wsadr, 2)   # Receive at the same spot

    # Longest ADC conversion time
    r.poke(reg_admrc, 0x03)
    r.poke(reg_adrlc, 0x01)

    # Pre-load packet header
    r.poke(ep1_buffer + 0, 2)
    r.poke(reg_ep1cnt, 9)

    return r

def loop_func(precopy):
    r = Ropper()

    # Send USB packet (buffered in temp ram)
    r.memcpy(ep1_buffer + 1, factory_temp_ram, 8)
    r.le16(ep1sta_bit3_set)

    for bit in range(4):

        # A little delay to ensure ADC is ready
        precopy(r)

        r.poke(reg_wcon, 0xd0)     # Transmit / Zero
        r.delay(0.1)
        r.poke(reg_wcon, 0xb0)     # Receive / Integrate
        r.delay(0.2)

        # Store previous ADC result
        r.memcpy(factory_temp_ram + bit*2, reg_adrlc, 2)

        r.adc_start()

    return r

if __name__ == '__main__':
    write_loop(setup_func(), loop_func)
