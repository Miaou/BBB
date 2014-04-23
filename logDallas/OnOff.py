#!/usr/bin/python3

import Adafruit_BBIO.GPIO as gpio
from multiprocessing import Value
import time

class OnOff:
    def __init__(self, pin, trigger_value, mode=True, init_value=gpio.LOW, debug=False):
        self.trigger = trigger_value
        self.mode = mode
        self.debug = debug
        self.pin = pin
        gpio.setup(self.pin, gpio.OUT, initial = init_value)

    def __del__(self):
        gpio.cleanup()
        if self.debug :
            print("Cleaning up all gpio's used")

    def run(self, value_to_check,stop, period = 10):
        'value_to_check and stop must be multiprocessing.Value'
        if self.debug:
            print("Starting OnOff checking")
        while not stop.value:
            if value_to_check.value > self.trigger:
                if self.mode:
                    gpio.output(self.pin, gpio.HIGH)
                    if self.debug:
                        print(self.pin, "set to HIGH")
                else:
                    gpio.output(self.pin, gpio.LOW)
                    if self.debug:
                        print(self.pin, "set to LOW")
            else:
                if self.mode:
                    gpio.output(self.pin, gpio.LOW)
                    if self.debug:
                        print(self.pin, "set to LOW")
                else:
                    gpio.output(self.pin, gpio.HIGH)
                    if self.debug:
                        print(self.pin, "set to HIGH")
            time.sleep(period)

        if self.debug:
            print("Ending OnOff checking")


if __name__ == '__main__':
    from threading import Thread
    test = OnOff("P9_16", 10,mode=False, debug=True)
    trigger = Value('f', 0)
    stop = Value('b', False)
    try:
        Thread(target=test.run, args=(trigger, stop, 5)).start()
    except KeyboardInterrupt:
        print("That's it")
        stop.value = True

