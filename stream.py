#!/usr/bin/env python3
"""\
Stream g-code to grbl controller
This script differs from the simple_stream.py script by 
tracking the number of characters in grbl's serial read
buffer. This allows grbl to fetch the next line directly
from the serial buffer and does not have to wait for a 
response from the computer. This effectively adds another
buffer layer to prevent buffer starvation.
CHANGELOG:
- 20140714: Updated baud rate to 115200. Added a settings
  write mode via simple streaming method. MIT-licensed.
TODO: 
- Add runtime command capabilities
---------------------
The MIT License (MIT)
Copyright (c) 2012-2014 Sungeun K. Jeon
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
---------------------
"""

import serial
import time
import sys
import argparse

from grbl_gamepad.interface import Grbl
from grbl_gamepad.protocol import SimpleProtocol
from grbl_gamepad.messages import *


# Define command line argument interface
parser = argparse.ArgumentParser(description='Stream g-code file to grbl. (pySerial and argparse libraries required)')
parser.add_argument('gcode_file', type=argparse.FileType('r'),
        help='g-code filename to be streamed')
parser.add_argument('device_file',
        help='serial device path')
parser.add_argument('-q','--quiet',action='store_true', default=False, 
        help='suppress output text')
parser.add_argument('-s','--settings',action='store_true', default=False, 
        help='settings write mode')        
args = parser.parse_args()

# Periodic timer to query for status reports
# TODO: Need to track down why this doesn't restart consistently before a release.
# def periodic():
#     s.write('?')
#     t = threading.Timer(0.1, periodic) # In seconds
#     t.start()

# Initialize
print(args.device_file)
s = serial.Serial(args.device_file,115200)
f = args.gcode_file
verbose = True
if args.quiet : verbose = False
settings_mode = False
if args.settings : settings_mode = True

# Wake up grbl
print("Initializing grbl...")

grbl = Grbl(s, protocol=SimpleProtocol, debug=True)

# def message_handler(message, grbl):
#         if isinstance(message, WelcomeMessage)

while not grbl.version:
        pass

grbl.query_status()

while not grbl.status['mode']:
    pass

if grbl.status['mode'] == 'Alarm':
    grbl.unlock()


# The entire file will be enqeued
for line in f:
        line = line.strip()
        #print(repr(line))
        grbl.send(line)

print("The program has been queued and will be run. Pause with CTRL-C")

# Wait until every line is sent
while not grbl.protocol.send_queue.empty():
    try:
        pass
    except KeyboardInterrupt:
        # use CTRL-C to halt Grbl
        #grbl.stop() # stop processing send queue; stop receiving messages
        grbl.send(b"!") # feed hold

        print("Press ENTER to resume the program")
        input("")

        grbl.send(b"~")
        #grbl.start()

# Wait for user input after streaming is completed
print("G-code streaming finished!\n")
print("WARNING: Wait until grbl completes buffered g-code blocks before exiting.")
input("  Press <Enter> to exit and disable grbl.") 
# Close file and serial port
f.close()
s.close()
