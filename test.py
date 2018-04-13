from grbl_gamepad.interface import Grbl
from serial import Serial
from time import sleep

g = Grbl(Serial('/dev/ttyACM0', baudrate=115200))

#sleep(3)

input("ENTER to quit")
