CTE-450 Homebrew
================

The CTE-450 (Bamboo Fun) tablet is cheap and widely available used, making it an interesting target for experimentation. It's also just barely old enough not to use any custom silicon designed by Wacom. Its microcontroller is a Sanyo/ONsemi LC871W32, with 32K of program memory (likely mask ROM) and 2K of RAM.

Its USB HID protocol includes many undocumented features, including the ability to write arbitrary data to RAM. With this, we can write our own programs for the tablet using return-oriented programming techniques.
