#!/usr/bin/env python

# Values here for firmware version 1.16
# Version 1.13 has also been observed, with different offsets.

# This should be reading from a var we can try writing
word_addr = 0x3ae

# 12 MHz xtal
fosc = 12e6

# An okay place to return from the stack smash
mainloop_safe_spot = 0x818

# RAM addresses
ep1_buffer = 0x280
stack_base = 0x443
timer0_funcptr = 0x39d
rop_addr = 0x4f0
counter_addr = 0x38c

# LC87 registers
reg_ie = 0xfe08
reg_t0cnt = 0xfe10
reg_t1cnt = 0xfe18
reg_p3 = 0xfe4c         # Bit0 = test point TP5
reg_adcrc = 0xfe58
reg_ep1cnt = 0xfe98
reg_wclkg = 0xfeb2

# Code gadgets
ret = 0x244
infinite_loop = 0x1ac
ldw_spl_popw_r0 = 0x26f1
popw_spl_r0 = 0x7d6
popw_r0 = 0x2a2c
popw_r3 = 0xe1b
popw_r2_r3_r4 = 0x013cb
copy_codememR3_ramR2_countR4 = 0x2a30
stw_r3_ep0ack_ld04_popw_r2_r4_r5_r7_r6 = 0x23ec
st_r1_ep0ackstall_popw_r2 = 0x1e42
timer0_disable = 0x29ca
adc_shutdown = 0xb89
memcpy_destR2_srcR3_countR4 = 0x29e0
feb0_loader = 0xb97
ep1sta_bit3_set = 0x25e1
incw_counter_popw_r2_r3_r4 = 0x13c8
r0_to_counter_popw_r2_r3 = 0xe12

# Lookup table for finding arbitrary bytes in code memory
# missing values: 52 D2
byte_gadgets = [
    0x0044, 0x0002, 0x00a1, 0x009f, 0x009e, 0x009d, 0x0128, 0x009c,
    0x009b, 0x009a, 0x0176, 0x0025, 0x0098, 0x00b2, 0x0097, 0x0096,
    0x00be, 0x0095, 0x00ca, 0x0094, 0x00d2, 0x0093, 0x00dc, 0x0092,
    0x00e4, 0x0091, 0x00ec, 0x0090, 0x00f4, 0x00f8, 0x008f, 0x0102,
    0x0000, 0x010a, 0x010e, 0x008d, 0x01dd, 0x008c, 0x02da, 0x0258,
    0x008b, 0x0259, 0x0015, 0x002d, 0x0045, 0x0089, 0x04fb, 0x025c,
    0x0088, 0x02df, 0x025d, 0x004c, 0x025e, 0x0086, 0x025f, 0x02e2,
    0x0085, 0x0261, 0x02e4, 0x0084, 0x02e5, 0x0263, 0x0083, 0x0220,
    0x03f1, 0x0082, 0x0173, 0x0160, 0x0081, 0x0267, 0x07b8, 0x0080,
    0x07eb, 0x02eb, 0x007f, 0x02ec, 0x026a, 0x007e, 0x0139, 0x01d8,
    0x026c, 0x007d, None,   0x026e, 0x007c, 0x026f, 0x0839, 0x007b,
    0x0589, 0x0271, 0x007a, 0x0272, 0x02f5, 0x0079, 0x1544, 0x0274,
    0x0078, 0x02f7, 0x0275, 0x0077, 0x0276, 0x02f9, 0x0277, 0x0076,
    0x01b6, 0x0279, 0x0075, 0x027a, 0x063e, 0x0074, 0x1be0, 0x027c,
    0x0073, 0x02ff, 0x0001, 0x0072, 0x0301, 0x027f, 0x0071, 0x0280,
    0x05ca, 0x0070, 0x1ad8, 0x0304, 0x006f, 0x0305, 0x0283, 0x006e,
    0x01df, 0x006d, 0x01be, 0x01b9, 0x006c, 0x01b7, 0x0014, 0x006b,
    0x01b8, 0x0187, 0x006a, 0x028a, 0x0069, 0x028b, 0x030e, 0x0068,
    0x030f, 0x0067, 0x01e5, 0x028e, 0x0066, 0x028f, 0x0065, 0x0175,
    0x0185, 0x0064, 0x0291, 0x0063, 0x0315, 0x0062, 0x0316, 0x0061,
    0x0186, 0x0060, 0x0295, 0x005f, 0x0296, 0x005e, 0x005d, 0x0298,
    0x005c, 0x005b, 0x0148, 0x005a, 0x0059, 0x0058, 0x014e, 0x0057,
    0x0056, 0x0054, 0x0053, 0x0051, 0x004e, 0x0034, 0x02a0, 0x0b2d,
    0x0242, 0x02a1, 0x02a2, 0x02a3, 0x0610, 0x02a4, 0x0327, 0x02a5,
    0x037d, 0x02a6, 0x1875, 0x02a7, 0x032a, 0x02a8, 0x032b, 0x02a9,
    0x07f0, 0x02aa, 0x02ab, 0x032e, 0x02ac, 0x0b64, 0x02ad, 0x0331,
    0x02ae, 0x02af, None,   0x02b0, 0x001c, 0x02b1, 0x02b2, 0x0335,
    0x02b3, 0x003c, 0x013c, 0x0337, 0x0338, 0x02b5, 0x02b6, 0x01aa,
    0x02b7, 0x02b8, 0x19f7, 0x033c, 0x02b9, 0x02ba, 0x0747, 0x0745,
    0x02bc, 0x02bd, 0x02be, 0x0740, 0x02bf, 0x0757, 0x0024, 0x0343,
    0x02c1, 0x02c2, 0x02c3, 0x0346, 0x02c4, 0x0347, 0x02c5, 0x0191,
    0x05f2, 0x0737, 0x0736, 0x075f, 0x06bb, 0x0784, 0x0177, 0x0003
]


def write_block(addr, bytes):
    print '%04x %s' % (addr, ' '.join(['%02x' % b for b in bytes]))

def write(addr, bytes):
    while bytes:
        write_block(addr, bytes[:0x10])
        addr += 0x10
        bytes = bytes[0x10:]


class Reloc:
    def __init__(self, offset=0, shift=0):
        self.offset = offset
        self.shift = shift

    def link(self, base_addr, index):
        #print "link %d %d %04x %04x" % (self.offset, self.shift, base_addr, index)
        return 0xff & ((self.offset + base_addr + index) >> self.shift)


class Ropper:
    def __init__(self):
        self.bytes = []

    def link(self, base_addr):
        result = []
        for i in range(len(self.bytes)):
            b = self.bytes[i]
            if isinstance(b, Reloc):
                result.append(b.link(base_addr, i))
            else:
                result.append(int(b))
        return result

    def le16(self, word):
        self.bytes = [word & 0xFF, word >> 8] + self.bytes

    def nop(self, count = 1):
        while count > 0:
            self.le16(ret)
            count -= 1

    def rel16(self, offset = 0):
        self.bytes = [Reloc(offset), Reloc(offset-1, shift=8)] + self.bytes

    def jmp(self, sp):
        self.le16(popw_spl_r0)
        self.le16(sp + 2)

    def set_r0(self, r0):
        self.le16(popw_r0)
        self.le16(r0)

    def set_r2_r3_r4(self, r2, r3, r4):
        self.le16(popw_r2_r3_r4)
        self.le16(r2)
        self.le16(r3)
        self.le16(r4)

    def memcpy(self, dest, src, count):
        self.set_r2_r3_r4(dest, src, count)
        self.le16(memcpy_destR2_srcR3_countR4)

    def copy_from_codemem(self, dest, src, count):
        self.set_r2_r3_r4(dest, src, count)
        self.le16(copy_codememR3_ramR2_countR4)

    def memcpy_indirect_src(self, dest, src_ptr, count):
        # memcpy a new src into the memcpy below
        self.le16(popw_r2_r3_r4)
        self.rel16(-2*6)
        self.le16(src_ptr)
        self.le16(2)
        self.le16(memcpy_destR2_srcR3_countR4)

        self.le16(popw_r2_r3_r4)
        self.le16(dest)
        self.le16(0)  # rel target
        self.le16(count)
        self.le16(memcpy_destR2_srcR3_countR4)

    def delay(self, millisec):
        # memcpy is pretty slow, try to do a nop with it
        v = int(round(102 * millisec))
        while v > 0:
            q = min(v, 0x3000)
            self.memcpy(0xc000, 0xc000, q)
            v -= q

    def poke(self, dest, byte):
        self.copy_from_codemem(dest, byte_gadgets[byte], 1)

    def get_stuck(self):
        self.le16(infinite_loop)

    def debug_pulse(self, count = 1):
        for i in range(count):
            self.poke(reg_p3, 0)
            self.poke(reg_p3, 1)

    def ep1_send(self, count):
        self.poke(reg_ep1cnt, count)
        self.le16(ep1sta_bit3_set)

    def ep1_poke(self, bytes):
        for i in range(len(bytes)):
            self.poke(ep1_buffer + i, bytes[i])
        self.ep1_send(len(bytes))

    def ep1_mouse_packet(self):
        self.poke(ep1_buffer + 0, 1)
        self.ep1_send(5)

    def set_wclk_freq(self, hz):
        n = int(round((fosc / 2.0 / hz) - 1))
        assert n >= 0
        assert n <= 0xff
        self.poke(reg_wclkg, n)

    def set_counter(self, value):
        self.set_r0(value)
        self.le16(r0_to_counter_popw_r2_r3)
        self.le16(0)
        self.le16(0)

    def inc_counter(self):
        self.le16(incw_counter_popw_r2_r3_r4)
        self.le16(0)
        self.le16(0)
        self.le16(0)

    def irq_global_disable(self):   self.poke(reg_ie, 0)
    def irq_global_restore(self):   self.poke(reg_ie, 0x8C)
    def irq_disable_timer0(self):   self.poke(reg_t0cnt, 0)
    def irq_disable_timer1(self):   self.poke(reg_t1cnt, 0)
    def irq_disable_adc(self):      self.poke(reg_adcrc, 0)

    def irq_disable_tablet(self):
        self.irq_global_disable()
        self.irq_disable_timer0()
        self.irq_disable_timer1()
        self.irq_disable_adc()
        self.irq_global_restore()

    def set_mux_latches(self, select_bits, enable_bits):
        assert select_bits >= 0 and select_bits <= 7
        assert enable_bits >= 0 and enable_bits <= 0xF
        enable_bits ^= 0xF
        word = (select_bits << 3) | (enable_bits << 6)
        self.poke(0xfeba, word & 0xFF)
        self.poke(0xfebb, word >> 8)
        self.memcpy(0xfeb8, 0xfeba, 2)

    def set_mux_from_ram(self, addr):
        self.memcpy(0xfeba, addr, 2)
        self.memcpy(0xfeb8, 0xfeba, 2)

    def set_mux_from_codemem(self, addr):
        self.copy_from_codemem(0xfeba, addr, 2)
        self.memcpy(0xfeb8, 0xfeba, 2)


def make_slide(entry):
    r = Ropper()
    r.nop(6)
    r.jmp(entry)
    assert len(r.bytes) == 0x10
    return r


def make_looper(base_addr, setup_code, body_code):
    # Executing code destroys it, we have to make copies.

    def trampoline(dest, src, size):
        r = Ropper()
        r.memcpy(dest, src, size)
        r.jmp(dest + size - 1)
        return r.bytes

    trampoline_size = len(trampoline(0,0,0))

    # We'll need to include room for 2 extra trampolines with the body,
    # the one used to restore the setup trampoline, and the setup trampoline itself.
    augmented_body_size = 2 * trampoline_size + len(body_code.bytes)

    # Now we can lay out the address space
    addr_setup_trampoline = base_addr
    addr_setup_code = addr_setup_trampoline + trampoline_size
    addr_augbody_orig = addr_setup_code + len(setup_code.bytes)
    addr_augbody_copy = addr_augbody_orig + augmented_body_size
    body_copy_baseaddr = addr_augbody_copy + 2 * trampoline_size

    setup_trampoline = trampoline(addr_augbody_copy, addr_augbody_orig, augmented_body_size)
    restore_trampoline = trampoline(addr_setup_trampoline, addr_augbody_orig, trampoline_size)

    augmented_body = setup_trampoline + restore_trampoline + body_code.link(body_copy_baseaddr)
    assert len(augmented_body) == augmented_body_size
    return (setup_trampoline + setup_code.link(addr_setup_code) + augmented_body, addr_augbody_orig - 1)


def feb0_loader_test(r):
    # Code fragment intended for factory test maybe?
    write(0x100, [  #   B0h  -> FEB0h_WCON
        0x00,       # [100h] -> FEB1h_WMOD
        0x07,       # [101h] -> FEB2h_WCLKG
        0x4a,       # [102h] -> FEB3h_WSND
        0xaf,       # [103h] -> FEB4h_WRCV
        0x7f,       # [104h] -> FEB5h_WWAI
        0x32,       # [105h] -> FEB6h_WCDLY0
        0x70,       # [106h] -> FEB8h_WSADRL
        0x06,       # [107h] -> FEB7h_WCDLY1
        0x02,       # [108h] -> FEB9h_WSADRH
        0x70,       # [109h] -> FEBAh_WRADRL
        0x02,       # [10ah] -> FEBBh_WRADRH
        0xfc,       # [10bh] -> FEBCh_WPMR0
        0x03,       # [10ch] -> FEBDh_WPMR1
        0xf1,       # [10dh] -> FEBEh_WPMR2
        0x00,       # [10eh] -> FEBFh_WPLLC
    ])              #   F1h  -> FEB0h_WCON
    r.le16(feb0_loader)

# SFR 0xfeb0:
#     Undocumented hardware starting here, something specfic to the 'W' series
#     LC871 chips, which don't have a public data sheet. Guessing that this is
#     a one-wire interface with some proprietary Sanyo/ONsemi format; I think
#     it's the same one used by the TCB87-TypeC debug interface, but here it's
#     being reused afaict mostly to generate the 750 kHz modulation pulses.
#     Names here were gleaned from data files included with the toolthain.
#
# 7       6       5       4       3       2       1       0       reg
# ----------------------------------------------------------------------------
#
# EN      GO      REP1    CHGP                    ctrl?   REP2    FEB0h_WCON      Control reg
#
#   EN        Peripheral master enable
#   GO        Trigger serial engine
#   REP1      After a delay (WWAI) go from receive back to transmit, change parallel word
#   CHGP      Enable V- chargepump output on P02 (independent from serial engine?)
#   REP2      Similar to REP1?
#
# (init to 00h)                                                   FEB1h_WMOD      Communication mode?
#
# Divisor, 8-bit. Fclk = Fosc / 2 / (1 + N)                       FEB2h_WCLKG     Clock gen config
#
# Number of clock cycles to transmit for                          FEB3h_WSND      Send counter
# Number of clocks to receive/integrate for                       FEB4h_WRCV      Receive counter
# Wait time between receive and repeated send                     FEB5h_WWAI      Wait counter
#
# (init to 32h)                                                   FEB6h_WCDLY0    Delay config?
#
# ack?    flag?   flag?   flag?           mode?           mode?   FEB7h_WCDLY1
#
# Parallel word to latch out just before send                     FEB8h_WSADRL    Parallel data word
#    Modified in an unknown way during REPEAT transmit            FEB9h_WSADRH
# Parallel word to latch out just before receive                  FEBAh_WRADRL    Parallel data word
#                                                                 FEBBh_WRADRH
#
# (init to 00h near gpio setup, FCh near use)                     FEBCh_WPMR0     Pin mapping bits?
# (init to 00h near gpio setup, 03h near use)                     FEBDh_WPMR1
# (init to F0h near gpio setup, F1h near use)                     FEBEh_WPMR2
#
# (unused except by factory test support)                         FEBFh_WPLLC     PLL for higher freq?
#
# The word-wide ports WSADR and WRADR are both set (sometimes by writing twice,
# others by copying from WRADR to WSADR after writing WRADR) from model-specific
# tables of multiplexer control values. Marked below as WRS.<bit>
#
# Pins:
# ("W" pins seem to be controlled directly by FEB0h hardware)
#
#     1     P73                     Touch ring drive output
#     2     /RES             TP10   Reset RC circuit
#     3     AN10                    10k pull-down resistor
#     4     AN11             TP8    Touch ring analog input
#     5     VSS              TP15
#     6     XTAL                    12 MHz xtal
#     7     XTAL
#     8     VDD
#     9     P10                     N/C
#     10    P11                     Power control
#     11    P12                     Button SW1, active low
#     12    P13                     Button SW3, active low
#
#     13    P14                     Button SW2, active low
#     14    P15                     Button SW4, active low
#     15    P16                     10k pull-down resistor
#     16    P17                     N/C, unused driven output
#     17    PWM1                    LEDs
#     18    PWM0                    LEDs
#     19    VDD
#     20    VSS
#     21    AN0              TP11   Analog integrator input
#     22    P01          W          Integrator reset: when high, integrator quickly falls to zero
#     23    P02          W          -V charge pump output (independent freq/phase)
#     24    P03          W          Direction: low=output, high=input
#
#     25    P04          W          Modulation clock output (usually 750 kHz when active)
#     26    P05                     N/C, unused driven output
#     27    P06                     N/C, unused driven output
#     28    P07                     Input, 10K pull-down on CTE-450 (part of model-select?)
#     29    P20      WRS.9          Mux enable output 3, active low
#     30    P21      WRS.8          Mux enable output 2, active low
#     31    P22      WRS.7          Mux enable output 1, active low
#     32    P23      WRS.6          Mux enable output 0, active low
#     33    P24      WRS.5          Mux select output bit 2
#     34    P25      WRS.4          Mux select output bit 1
#     35    P26      WRS.3          Mux select output bit 0
#     36    P27      WRS.2          N/C, weakly driven output?
#
#     37    D-                      USB Data
#     38    D+
#     39    VDD
#     40    VSS
#     41    UFILT                   USB Filter
#     42    P33                     N/C, unused driven output
#     43    P32              TP3    DBGP2, unused driven output
#     44    P31              TP4    DBGP1, unused driven output
#     45    P30              TP5    DBGP0 / Test sync out
#     46    DPUP                    USB Pull-up
#     47    P71                     Touch ring drive output
#     48    P72                     Touch ring drive output
#

def setup_func():
    r = Ropper()
    r.irq_disable_tablet()
    r.set_counter(0)
    r.set_wclk_freq(125000)     # Carrier frequency
    r.poke(0xfeb3, 255)         # Transmit length
    r.poke(0xfeb4, 5)           # Receive length
    r.poke(0xfeb5, 0)           # Repeat delay
    r.poke(0xfeb0, 0x90)        # Enabled, charge pump on
    r.poke(0xfeb0, 0xd1)        # Go, repeat
    return r

def loop_func():
    r = Ropper()
    r.irq_disable_tablet()

    # Heartbeat counter over USB
    r.inc_counter()
    r.inc_counter()
    r.inc_counter()
    r.inc_counter()
    r.inc_counter()
    r.inc_counter()
    r.inc_counter()
    r.inc_counter()
    r.memcpy(ep1_buffer+1, counter_addr, 2)
    r.ep1_mouse_packet()

#    r.set_mux_from_ram(counter_addr)
    r.set_mux_latches(3, 2|8)

    r.debug_pulse()
    r.delay(150)

    # Memory readback experiment
    #r.memcpy_indirect_src(ep1_buffer+3, counter_addr, 2)

    # feb0 hardware investigation
    #r.memcpy(ep1_buffer+1, 0xfeb8, 4)

    #adr = 0xfeb2
    #r.memcpy_indirect_src(adr, counter_addr+1, 1)

    #r.debug_pulse()
    #r.poke(0xfeb3, 0x4a)

    # Load new parallel output mapped to muxes
    # Crudely scans through mux states...
    #r.memcpy(0xfeba, counter_addr, 2)
    #r.memcpy(0xfeb8, 0xfeba, 2)

    # strobe?!
    #r.debug_pulse()
    #r.poke(0xfeb0, 0b10010000)    # Starts charge pump
    #r.debug_pulse()
    #r.poke(0xfeb0, 0b11000001)    # Stops charge pump, starts clock, latches mux, zero enable
    #r.debug_pulse()
    #r.poke(0xfeb0, 0b11010001)    # ireset as open collector, chgpump enable again
    #r.debug_pulse()

    # # Clear parallel output
    # r.poke(0xfeba, 0)
    # r.poke(0xfebb, 0)
    # r.memcpy(0xfeb8, 0xfeba, 2)

    # # strobe?!
    # r.poke(0xfeb0, 0x90)
    # r.poke(0xfeb0, 0xc1)

    return r


def write_loop(base_addr, setup_code, body_code):
    # Make a code fragment that runs repeatedly
    looper, entry = make_looper(base_addr, setup_code, body_code)
    write(base_addr, looper)
    write(stack_base, make_slide(entry).bytes)

if __name__ == '__main__':
    write_loop(rop_addr, setup_func(), loop_func())
