#/usr/bin/python
# Py2!!!


from Adafruit_BBIO import GPIO
from threading import Thread
from multiprocessing import Value
import time

PIN = 'P9_23'
bEnd = Value('b', False)
iCmd = Value('i', 0)


# Pseudo PWM, 0-100
def workerCommand(iCmd, bEnd):
    PERIOD = 10
    t0 = time.time()
    while not bEnd.value:
        print 'Control @', iCmd.value
        t1g = t0 + PERIOD*iCmd.value/100
        GPIO.output(PIN, GPIO.HIGH)
        while time.time() < t1g and not bEnd.value:
            time.sleep(.1)
        GPIO.output(PIN, GPIO.LOW)
        while time.time()-t0 < PERIOD and not bEnd.value:
            time.sleep(.1)
        t0 += PERIOD
        assert time.time()-t0 < PERIOD, "Command is lost"
    print('Ending control')


GPIO.setup(PIN, GPIO.OUT)
Thread(target=workerCommand, args=(iCmd, bEnd)).start()
print('bEnd.value = True')
