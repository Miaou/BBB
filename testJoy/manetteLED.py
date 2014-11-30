#
# Test du XBOX 360 CONTROLLER TO LIGHT UP A LED !!!

from Adafruit_BBIO import GPIO, PWM
from evdev import InputDevice, ecodes, categorize
from threading import Thread
#import select
import time



PWM_LED = 'P9_42'


axX = 0
bEnd = False

# C'est lourd d'utiliser evdev parce qu'il faut se wrapper les touches
def workerReadJoy():
    global axX,bEnd
    joy = InputDevice('/dev/input/event1')
    for event in joy.read_loop():
        if event.type in (ecodes.EV_KEY,ecodes.EV_ABS):
            #ev = categorize(event)
            #return ev,joy
            if event.type == ecodes.EV_ABS:
                if event.code == ecodes.ABS_RX:
                    axX = event.value
                    #print(axX)
            elif event.type == ecodes.EV_KEY:
                if event.code == ecodes.BTN_A:
                    print('Ending read loop')
                    bEnd = True
                    return


#a = workerReadJoy
th = Thread(target=workerReadJoy)
th.start()



PWM.start(PWM_LED, 0)
try:
    while not bEnd:
        PWM.set_duty_cycle(PWM_LED, max([abs(axX)-8192,0])/245.76)
        time.sleep(.001)
except KeyboardInterrupt:
    print('End Ctrl Loop')
finally:
    PWM.cleanup()


