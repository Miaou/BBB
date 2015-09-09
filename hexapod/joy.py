#!/usr/bin/python3

# My convenience functions for joy interfacing. Independant of the hexapod, in fact...


from evdev import InputDevice, ecodes
import time
import curses

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
#   (our task is not real-time sensitive, and the overhead is not that much)

from evdev._input import ioctl_capabilities # Sole parameter: InputDevice.fd

def getAxesValues(dev):
    # Yes, this is "kind of" brutal, but who cares...
    # 1) Get _rawcapabilities (via ioctl_[...])
    # 2) Take EV_ABS part out of it, which is a list [(iAxis, tAbsInfo), ...]
    # 3) Reform the list as a more usable dict
    return {iAxis:tAbsInfo[0] for iAxis,tAbsInfo in ioctl_capabilities(dev.fd)[ecodes.EV_ABS]} # In fact, we don't need InputDevice

def getNormValues(dev, dDeadZones):
    'dDeadZones = {ecodes.ABS_X:.25,...}'
    dAbsInput = getAxesValues(dev)
    fdz = lambda v,z: ((v<-z or v>z) and ( (v<-z and (v+z)) or (v>z and (v-z)) )) or 0
    return {i:fdz(v/dAbsMax[i],dDeadZones[i] if i in dDeadZones else 0)/(1.-(dDeadZones[i] if i in dDeadZones else 0.)) for i,v in dAbsInput.items()}

def getFallingBtns(dev):
    'Returns falling edges (buttons being pushed)'
    try:
        events = list(dev.read())
    except IOError:
        events = []
    return [ev.code for ev in events if ev.type == ecodes.EV_KEY and ev.value == 1] # value is 0 for up, 1 for down, 2 for hold


try:
    dev = InputDevice('/dev/input/event1') # Hardcoded, but, hey, it's only for the BBB
except OSError as e:
    print('----> Did you run xboxdrv? <----')
    raise e

dAbsMax = {i:absInfo.max for i,absInfo in dev.capabilities()[ecodes.EV_ABS]}


if __name__=='__main__':
    # Old stuff
    def testRawCapa():
        POLL_PERIOD = .5
        t0 = time.time()
        while True:
            if time.time()-t0 > POLL_PERIOD:
                dAbsInputs = getAxesValues(dev)
                print('  '.join('{}: {:<6}'.format(ecodes.ABS[k][4:],v) for k,v in dAbsInputs.items()))
                t0 += POLL_PERIOD
            time.sleep(.01)
    
    def displayJoy(stdscr, dev):
        stdscr.addstr(0,0,'--> Start to Quit <--')
        while not ecodes.BTN_START in dev.active_keys():
            dAbsInput = getAxesValues(dev)
            stdscr.move(1,0)
            stdscr.addstr('Active btns: '+' '.join(str(ecodes.BTN[i]) for i in dev.active_keys())+'\n')
            stdscr.addstr('Axes values:\n')
            for i,f in dAbsInput.items():
                stdscr.addstr('  {}: {}\n'.format(ecodes.ABS[i],f))
            stdscr.refresh()
            time.sleep(.1)

    curses.wrapper(displayJoy, dev)






