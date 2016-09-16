#!/usr/bin/env python

from roplib import *

def setup_func():
    r = Ropper()

    # Global disable while we're setting up
    r.irq_global_disable()

    # Turn off all IRQs except vector_23 (used by FEB0h peripheral)
    # We keep using part of that interrupt handler to trigger the ADC
    # and store its result.

    r.irq_disable_timer0()
    r.irq_disable_timer1()
    r.irq_disable_adc()
    r.irq_disable_pwm()
    r.irq_disable_usb()
    r.irq_disable_basetimer()

    # Stub out the callback that is usually invoked after storing the ADC result
    r.poke(ep1flags, 1)         # One-shot flag, triggers ADC on next FEB0h interrupt. Retrigger in the FEB0h ADC callback.
    r.poke(scanflags, 0)        # Make sure we don't disable scanning in the FEB0h ADC callback.
    r.pokew(scan_postadc_callback, ret)

    # Set up FEB0h peripheral
    r.poke(reg_wcon, 0xb0)              # Enabled, wait enabled, charge pump on
    r.set_wclk_freq(125000)             # Carrier frequency
    r.poke(reg_wsnd, 8)                 # Transmit length (fraction of a bit)
    r.poke(reg_wrcv, 127)               # Receive length (max)
    r.poke(reg_wwai, 127)               # Repeat delay / ADC conversion time (max)
    r.pokew(reg_wsadr, 0x158)           # Where to transmit (X12)
    r.memcpy(reg_wradr, reg_wsadr, 2)   # Receive at the same spot

    # Pre-load packet header
    r.poke(ep1_buffer + 0, 2)
    r.poke(reg_ep1cnt, 9)

    # Initiate scanning & repeat
    r.poke(reg_wcon, 0xf1)

    r.irq_global_restore()

    return r

def loop_func(precopy):
    r = Ropper()

    # Send USB packet
    r.le16(ep1sta_bit3_set)

    for bit in range(4):

        # Store the previous result
        r.memcpy(ep1_buffer + 1 + bit*2, reg_adrlc, 2)

        # Wait for the FEB0h interrupt, indicating RX completion.
        # The ISR will start the ADC for us.
        r.irq_wait()

        r.debug_out(bit & 1)

        # Spread out the loop overhead
        if bit == 0: precopy(r, 0x18)
        if bit == 1: precopy(r, 0x20)
        if bit == 2: precopy(r, 0x30)

    return r

if __name__ == '__main__':
    write_loop(setup_func(), loop_func)
