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
        self.state = 0

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
                    self.state = 1
                    if self.debug:
                        print(self.pin, "set to HIGH")
                else:
                    gpio.output(self.pin, gpio.LOW)
                    self.state = 0
                    if self.debug:
                        print(self.pin, "set to LOW")
            else:
                if self.mode:
                    gpio.output(self.pin, gpio.LOW)
                    self.state = 0
                    if self.debug:
                        print(self.pin, "set to LOW")
                else:
                    gpio.output(self.pin, gpio.HIGH)
                    self.state = 1
                    if self.debug:
                        print(self.pin, "set to HIGH")
            time.sleep(period)

        if self.debug:
            print("Ending OnOff checking")

    def runperiodic(self, stop, periodOn, periodOff):
        "Invert current state periodicly"
        if self.debug:
            print("Starting periodic checking")
        while not stop.value:
            gpio.output(self.pin, not self.state)
            self.state = not self.state
            if self.debug:
                print(self.pin, "switched state")
            
            if self.state:
                time.sleep(periodOn)
            else:
                time.sleep(periodOff)

        if self.debug:
            print("Ending OnOff checking")

if __name__ == '__main__':
    from threading import Thread
    test = OnOff("P8_15", 0.5,mode=False, debug=True)
    trigger = Value('b', 0)
    stop = Value('b', False)
    try:
        Thread(target=test.runperiodic, args=(stop, 3, 1)).start()
    except KeyboardInterrupt:
        print("That's it")
        stop.value = True

