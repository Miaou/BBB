#!/usr/bin/python
# -*- coding: utf-8 -*-
# Reads the IR-temperature sensor
# (qui finalement est compatible i2c, et le repeated-start, ben ... osef ^^')


import smbus
import time


# By default, the IR is at 0x5A

ADDR = 0x5A

bus = smbus.SMBus(1) # I²C port 2 in headers (P9_19 & 20) is bus 1... This may be because I²C bus 0 is "internal"

def fetch_print():
    print 'Ta: {:.2f}\nTo: {:.2f}'.format(bus.read_word_data(ADDR, 0x06)*0.02-273.15,
                                          bus.read_word_data(ADDR, 0x07)*0.02-273.15)
    # RAM adress 0x08 is 0 on my device. There are MLX where there are 2 oriented sensors...


while True:
    fetch_print()
    time.sleep(.5)
    # Bus may have to be recreated if there is an error "I2C not available"
