all: poker

HIDAPI := /usr/local/Cellar/hidapi/0.8.0-rc1

CFLAGS += -I$(HIDAPI)/include/
CFLAGS += $(HIDAPI)/lib/libhidapi.a -framework IOKit -framework CoreFoundation
