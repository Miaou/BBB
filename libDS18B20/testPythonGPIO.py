#!/usr/bin/python

import time
from Adafruit_BBIO import GPIO


O_TEST = 'P9_13'



def testTimeN():
    N = 0
    t0 = time.time()
    while True:
        t1 = time.time()
        N += 1
        if t1-t0 > .001:
            break
    print(t1-t0, N)

def testSleep():
    t0 = time.time()
    time.sleep(.001)
    print(time.time()-t0)



for i in range(10):
    testTimeN()
print()
for i in range(10):
    testSleep()

GPIO.setup(O_TEST, GPIO.OUT)
GPIO.output(O_TEST, GPIO.LOW)
def testSwitch():
    t0 = time.time()
    GPIO.output(O_TEST, GPIO.HIGH)
    GPIO.output(O_TEST, GPIO.LOW)
    t1 = time.time()
    t2 = time.time()
    print(t1-t0, t2-t1)

print()
for i in range(10):
    testSwitch()
