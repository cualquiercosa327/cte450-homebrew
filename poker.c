#include <unistd.h>
#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <hidapi/hidapi.h>

// Currently unused experiment; getting data back via HID works better
static const bool word_readback = false;

void write_ram(hid_device *handle, uint16_t addr, uint8_t block[16]);
uint16_t read_word(hid_device *handle);
void show_device_strings(hid_device *handle);
hid_device *find_tablet();
void little_delay();

int main()
{
	hid_device *handle = find_tablet();
	show_device_strings(handle);

	if (word_readback) {
		printf("word: %04X\n", read_word(handle));
	}

	char *line = 0;
	size_t linecap = 0;
	ssize_t linelen;
	while ((linelen = getline(&line, &linecap, stdin)) > 0) {
		char *hexdata;
		int addr = strtoul(line, &hexdata, 16);
		uint8_t block[16] = { 0 };
		for (int i = 0; hexdata && i < 16; i++) {
			block[i] = strtoul(hexdata, &hexdata, 16);
		}
		write_ram(handle, addr, block);
		little_delay();
	}

	if (word_readback) {
		for (int i = 0; i < 10; i++) {
			little_delay();
			printf("word: %04X\n", read_word(handle));
		}
	}

	hid_exit();
	return 0;
}

void little_delay()
{
	// Device seems to crash if we send these two quick;
	// not sure whose fault it is yet.
	usleep(10000);
}

hid_device *find_tablet()
{
	hid_device *handle;

	hid_init();

	handle = hid_open(0x56a, 0x17, NULL);
	if (!handle) {
		perror("nope");
		exit(1);
	}

	return handle;
}

void write_ram(hid_device *handle, uint16_t addr, uint8_t block[16])
{
	uint8_t rep10[3] = { 0x10 };
	uint8_t rep11[17] = { 0x11 };

	rep10[1] = addr >> 8;
	rep10[2] = addr & 0xFF;
	memcpy(&rep11[1], block, 16);

	printf("Writing %04x,", addr);
	for (unsigned i = 0; i < 16; i++) {
		printf(" %02x", block[i]);
	}
	printf("\n");

	// Set a write pointer
	if (hid_send_feature_report(handle, rep10, sizeof rep10) < 0) {
		perror("blarr");
		exit(2);
	}

	// Write exactly 16 bytes
	if (hid_send_feature_report(handle, rep11, sizeof rep11) < 0) {
		perror("seriously?");
		exit(3);
	}
}

uint16_t read_word(hid_device *handle)
{
	uint8_t rep10[4] = { 0x10 };

	if (hid_get_feature_report(handle, rep10, sizeof rep10) != sizeof rep10) {
		perror("crunchy~");
		exit(4);
	}

	return (rep10[2] << 8) | rep10[3];
}

void show_device_strings(hid_device *handle)
{
	const int MAX_STR = 255;
	wchar_t wstr[MAX_STR];

	hid_get_manufacturer_string(handle, wstr, MAX_STR);
	wprintf(L"Manufacturer String: %ls\n", wstr);
	hid_get_product_string(handle, wstr, MAX_STR);
	wprintf(L"Product String: %ls\n", wstr);
}
