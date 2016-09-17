CTE-450 Homebrew
================

The CTE-450 (Bamboo Fun) tablet is cheap and widely available used, making it an interesting target for experimentation. It's also just barely old enough not to use any custom silicon designed by Wacom. Its microcontroller is a Sanyo/ONsemi LC871W32, with 32K of program memory (likely mask ROM) and 2K of RAM.

Its USB HID protocol includes many undocumented features, including the ability to write arbitrary data to RAM. With this, we can write our own programs for the tablet using return-oriented programming techniques.

Currently focusing on devices with firmware version **1.16**, as reported in the USB device descriptor.

Experiments here are a mess of shitty pipes that come apart easily for cleaning. Current ROP bits crash a lot during load; have a reset button handy.

	rop/sampler.py | host/sampler.js | tee wave.csv | host/detector.js | tee wave2.csv && host/plot.script
