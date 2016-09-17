#!/usr/bin/env python

from roplib import *

def setup_func():
    r = Ropper()
    r.irq_global_disable()
    return r

def loop_func(precopy):
    r = Ropper()
    r.debug_pulse()
    return r

if __name__ == '__main__':
    write_loop(setup_func(), loop_func)
