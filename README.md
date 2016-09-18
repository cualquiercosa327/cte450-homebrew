CTE-450 Homebrew
================

The CTE-450 (Bamboo Fun) tablet is cheap and widely available used, making it an interesting target for experimentation. It's also just barely old enough not to use any custom silicon designed by Wacom. Its microcontroller is a Sanyo/ONsemi LC871W32, with 32K of program memory.

Its USB HID protocol includes many undocumented features, including the ability to write arbitrary data to RAM. With this, we can write our own programs for the tablet using return-oriented programming techniques.

So far I've seen two versions of the device, **1.13** with flash and **1.16** with mask ROM. With some edits to the .py configuration files, this codebase should support both versions.

Experiments here are a mess of shitty pipes that come apart easily for cleaning. Current ROP bits crash a lot during load; have a reset button handy.

	rop/sampler.py | host/sampler.js | tee wave.csv | host/detector.js | tee wave2.csv && host/plot.script
