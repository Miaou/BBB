#!/usr/bin/python3

# Calibration of the legs using the XBox Controller (see xboxdrv in the ../doc) and evdev
# Small tool provided more than anything else "as-is", just for fun...


from evdev import InputDevice, ecodes
from config import lServos
from servos import PruInterface, ServoController


# InputDevice has a nice active_keys() which avoids the parsing of the events, but not abs_values()...
# This should not be THAT hard to add. However, I don't want to compile/test/install, and not very comfortable with the Python C-API.
# To do so, see https://github.com/gvalkov/python-evdev/blob/master/evdev/device.py,
#  -> active_keys() uses _input.ioctl_EVIOCGKEY(self.fd) (see https://github.com/gvalkov/python-evdev/blob/master/evdev/input.c)
#   and implementing a ioctl_EVIOCGABS should not be that hard
#  -> but abs values are also stored in the capabilities() (see device.py)
#   and this is generated when ._rawcapabilities is created,
#   and this is done by _input.ioctl_capabilities() (see input.c)
#   which has the code ready for EVIOCGABS
#  -> so we just have to call _input.ioctl_capabilities() and find the interesting value.
#   (our task is not real-time sensitive)

from evdev._input import ioctl_capabilities # Sole parameter: InputDevice.fd



dev = InputDevice('/dev/input/event1') # Hard-coded, don't care, calibration, small tool, fun with controller


import time

def testRawCapa():
    POLL_PERIOD = .5
    t0 = time.time()
    while True:
        if time.time()-t0 > POLL_PERIOD:
            dInputs = ioctl_capabilities(dev.fd) # In fact, we don't need InputDevice
            dAbsInputs = {iAxis:l[0] for iAxis,l in dInputs[ecodes.EV_ABS]}
            print('  '.join('{}: {:<6}'.format(ecodes.ABS[k][4:],v) for k,v in dAbsInputs.items()))
            t0 += POLL_PERIOD
        time.sleep(.01)


