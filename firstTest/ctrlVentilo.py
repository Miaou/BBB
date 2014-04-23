#
# :)

from Adafruit_BBIO import GPIO, PWM, ADC
from threading import Thread
import select
import time



AIN = 'AIN4'
#PWM_VENTILO = 'P8_46'
PWM_VENTILO = 'P9_42'
#IN_TACKY = 'P8_43'
IN_TACKY = 'P9_26'
ADC.setup()

#GPIO.setup(IN_TACKY, GPIO.IN)


def readCtrlLoop():
    PWM.start(PWM_VENTILO, 0)
    try:
        while True:
            val = ADC.read(AIN) # read_raw()
            PWM.set_duty_cycle(PWM_VENTILO, val*100)
            time.sleep(.001)
    except KeyboardInterrupt:
        print('Ok, end')
    PWM.cleanup()

def showTacky():
    GPIO.setup(IN_TACKY, GPIO.IN)
    PWM.start(PWM_VENTILO, 100)
    try:
        while True:
            print(GPIO.input(IN_TACKY))
            time.sleep(.5)
    except KeyboardInterrupt:
        print('Ok, end')
    PWM.cleanup()

# Simulating interrupts
def countSpeed():
    N = 0
    t0 = time.time()
    f = open('/sys/class/gpio/gpio14/value')
    poll = select.poll()
    poll.register(f, select.POLLERR | select.POLLPRI)
    try:
        while True:
            poll.poll(1000)
            f.read()
            f.seek(0)
            N += 1
            if time.time()-t0>1:
                t0 = time.time()
                print(N, N*60)
                if N == 1:
                    break
                N = 0
    except KeyboardInterrupt:
        f.close()
th = Thread(target=countSpeed)
th.start()

readCtrlLoop()

#showTacky()

