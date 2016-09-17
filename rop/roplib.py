# Firmware version still needs to be picked manually.
from gadgets_113 import *
#from gadgets_116 import *

# 12 MHz xtal
fosc = 12e6

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
        self.le16(pwm0_disable)
        self.le16(pwm1_disable)

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
    def precopy_placeholder(r, n_bytes=None):
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
    def precopy_fn(r, n_bytes=None, precopy_len=precopy_len):
        if n_bytes is None:
            # Max possible
            n_bytes = len(r.bytes) - precopy_len[0]
        assert n_bytes > 0
        next_precopy_len = precopy_len[0] + n_bytes
        assert next_precopy_len <= len(r.bytes)
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


def write_loop(setup_code, body_factory, base_addr=rop_addr):
    # Write a code fragment that runs repeatedly
    looper = make_looper(base_addr, setup_code, body_factory)
    entry = base_addr + len(looper) - 1
    write(base_addr, looper)
    write(stack_base, make_slide(entry).bytes)

