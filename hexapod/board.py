#!/usr/bin/python3
#

# The User Interface
# Made of control modes as UI-modules that will be in charge for a time...


import sys
sys.path.append(sys.path[0]+'../libServo')
from servos import ServoController
from config import lServos
from trajectory import WalkTrajectory
from joy import dev, ecodes, getNormValues
import curses
import time
from multiprocessing import Value





# Main controller, which should remember last position,
#  so that we have smooth transitions?
class UIMain:
    MODE_WALK = 0 # Useful?
    MODE_RISE = 1
    MODE_CALIBRATION = 2
    MODE_POSE = 3
    def __init__(self, dev):
        self.bServosOn = False
        self.iCurMode = UIMain.MODE_WALK
        self.lModes = [UIWalk(self)]
        self.nSetAngles = 0
        self.fLastFreq = 0.
        self.ftCheck = time.time()
        self.sctl = ServoController(lServos)
        self.dev = dev
        self.wndHead = curses.newwin(4,curses.COLS)
        self.onSizeChanged()
        self.bIsFinished = False
    def isFinished(self):
        'Signals a quit'
        return self.bIsFinished
    def getCurrentMode(self):
        return self.iCurMode
    def setAngles(self, lAngles):
        self.nSetAngles += 1
        if self.bServosOn:
            self.sctl.setAngles(lAngles)
        else:
            self.sctl.setAngles([None]*len(self.lServos))
    def step(self, t):
        'A step in time, reacts to inputs'
        global dDeadZones
        if t-self.ftCheck > .5:
            self.ftCheck += .5
            self.fLastFreq = self.nSetAngles/.5
            self.nSetAngles = 0
        lBtns = self.dev.active_keys()
        dNormInput = getNormValues(dev, dDeadZones)
        if ecodes.BTN_A in lBtns:
            self.iCurMode += 1
            self.iCurMode %= len(self.lModes)
            # TODO: Handle transition, call the new mode
            self.lModes[self.iCurMode].onSizeChanged()
            self.lModes[self.iCurMode].resume()
        elif ecodes.BTN_START in lBtns:
            self.bIsFinished = True
        # if ecodes.BTN_B # No, as calibration and other modes may require different key mapping
        if curses.getch() == curses.KEY_RESIZE:
            self.onSizeChanged()
            self.lModes[self.iCurMode].onSizeChanged()
        self.lModes[self.iCurMode].step(t, lBtns, dNormInput)
    def activateServos(self, bActive):
        self.bServosOn = bActive
    def onSizeChanged(self):
        self.wndHead.erase()
        self.wndHead.move(0,0)
        self.wndHead.resize(4,curses.COLS)
        sHead = ' SUPER HEXAPOD 3000 by Dr. PAB '
        nDash = (curses.COLS-len(sHead))//2
        self.wndHead.addstr('-'*nDash+sHead+'-'*nDash+'\n')
        self.wndHead.addstr('Mode:  walk\n') # rise calib pose
        self.wndHead.addstr('Servos:  OFF\n')
        self.wndHead.addstr('Refresh rate:  ff.f Hz (ff.f ms)')
    def refresh(self):
        'Refreshes the UI'
        self.wndHead.chgat(1,7,-1, curses.A_NORMAL)
        self.wndHead.chgat(1,(7,)[self.iCurMode],(4,)[self.iCurMode], curses.A_UNDERLINE)
        self.wndHead.move(2,9)
        self.wndHead.clrtoeol()
        self.wndHead.addstr('ON' if self.bServosOn else 'OFF', curses.A_REVERSE|(curses.color_pair(1) if self.bServosOn else curses.color_pair(2)))
        self.wndHead.addstr(3,14,'{:5.1f} Hz ({:3.1} ms)'.format(self.fLastFreq, 1000/self.fLastFreq))
        self.wndHead.noutrefresh()
        self.lModes[self.iCurMode].refresh()
        curses.doupdate()
        
        


# Base UI
# Why would main not be a base UI? Because it handles things differently.
# What is the interest of having a base UI? Only a common skeleton
class UIMode:
    def __init__(self, uiMain):
        self.uiMain = uiMain
    def resume(self): pass
    def step(self, t, lBtns, dNormInput): pass
    def onSizeChanged(self): pass
    def refresh(self): pass



class UIWalk(UIMode):
    def __init__(self, uiMain):
        super().__init__(uiMain)
        self.Vx = 0.
        self.Vy = 0.
        self.Omega = 0.
        self.deltaU = .5
        self.u = 0.
        self.traj = WalkTrajectory(-69,self.deltaU)
        self.wndCmd = curses.newwin(5,19,5,0)
        self.wndEff = curses.newwin(5,19,5,20)
        self.wndTiming = curses.newwin(3,15,10,0)
        self.wndParams = curses.newwin(5,15,13,0)
        self.wndHelp = curses.newwin(8,20,18,0)
        self.onSizeChanged()
        self.t0 = time.time()
    def onSizeChanged(self):
        self.wndCmd.erase()
        self.wndCmd.move(0,0)
        self.wndCmd.addstr('Command:\n     Vx: fff.f mm/s\n     Vy: fff.f mm/s\n      V: fff.f mm/s\n  Omega:  ff.f tr/s')
        self.wndEff.erase()
        self.wndEff.move(0,0)
        self.wndEff.addstr('Effective:\n     Vx: fff.f mm/s\n     Vy: fff.f mm/s\n      V: fff.f mm/s\n  Omega:  ff.f tr/s')
        self.wndTiming.erase()
        self.wndTiming.move(0,0)
        self.wndTiming.addstr('Timing:\n  ΔU:  f.ff s\n   u:  f.ff')
        self.wndParams.erase()
        self.wndParams.move(0,0)
        self.wndParams.addstr('Parameters:\n   z: fff.f mm\n   S: fff.f mm\n   r: fff.f mm\n   h: fff.f mm')
        self.wndHelp.erase()
        self.wndHelp.move(0,0)
        self.wndHelp.addstr('Commands:\n')
        self.wndHelp.addstr(' A: change mode')
        self.wndHelp.addstr(' B: activate servos') # May changed with modes
        self.wndHelp.addstr(' Right trigger axis: time forward')
        self.wndHelp.addstr(' Left trigger axis: time backward')
        self.wndHelp.addstr(' Left stick: planar move')
        self.wndHelp.addstr(' Right stick: rotation')
        self.wndHelp.addstr(' Start: quit') # May not change
    def resume(self):
        self.u = 0. # May be removed
        self.t0 = time.time()
    def step(self, t, lBtns, dNormInput):
        global lServos
        dt = t-self.t0
        self.u += 2/self.deltaU*dt*(dNormInput[ecodes.ABS_GAS]-dNormInput[ecodes.ABS_BRAKE])
        self.Vx = +dNormInput[ecodes.ABS_X]*40
        self.Vy = -dNormInput[ecodes.ABS_Y]*40
        self.Omega = -dNormInput[ecodes.ABS_RX]/5
        self.uiMain.setAngles(traj.getAngles(lServos,
                                             self.Vx,
                                             self.Vy,
                                             self.Omega,
                                             self.u))
        self.t0 = t
    def refresh(self):
        self.wndCmd.addstr(2,8,'{:6.1f}'.format(self.Vx))
        self.wndCmd.addstr(3,8,'{:6.1f}'.format(self.Vy))
        self.wndCmd.addstr(4,8,'{:6.1f}'.format((self.Vx**2+self.Vy**2)**.5))
        self.wndCmd.addstr(5,8,'{:6.1f}'.format(self.Omega))
        q = self.traj._computeActualSpeedRatio(self.Vx, self.Vy, self.Omega)
        attr = curses.color_pair(1) if q < 1 else curses.color_pair(2)
        self.wndEff.addstr(2,8,'{:6.1f}'.format(self.Vx*q), attr)
        self.wndEff.addstr(3,8,'{:6.1f}'.format(self.Vy*q), attr)
        self.wndEff.addstr(4,8,'{:6.1f}'.format((self.Vx**2+self.Vy**2)**.5)*q, attr)
        self.wndEff.addstr(5,8,'{:6.1f}'.format(self.Omega*q), attr)
        self.wndTiming.addstr(2,5,'{:6.2f}'.format(self.deltaU))
        self.wndTiming.addstr(3,5,'{:6.2f}'.format(self.u))
        self.wndParams.addstr(2,5,'{:6.2f}'.format(self.traj.z))
        self.wndParams.addstr(3,5,'{:6.2f}'.format(self.traj.S))
        self.wndParams.addstr(4,5,'{:6.2f}'.format(self.traj.r))
        self.wndParams.addstr(5,5,'{:6.2f}'.format(self.traj.h))
        self.wndCmd.noutrefresh()
        self.wndEff.noutrefresh()
        self.wndTiming.noutrefresh()
        self.wndParams.noutrefresh()
        self.wndHelp.noutrefresh()
        



def mainLoop(stdscr):
    curses.noecho()
    stdscr.nodelay(True)
    curses.init_pair(1,curses.COLOR_RED,curses.COLOR_BLACK)
    curses.init_pair(2,curses.COLOR_GREEN,curses.COLOR_BLACK)

    uiMain = UIMain(dev)
    t0 = time.time()
    while not uiMain.isFinished():
        t = time.time()
        uiMain.step(t)
        if t-t0 > .25:
            uiMain.refresh()
            t0 += .25

    print('Disable Servos, waiting a sec')
    uiMain.sctl.setAngles([None]*len(self.lServos), True)
    time.sleep(1) # Check that the bWait parameter works
    

if __name__=='__main__':
    dDeadZones = {i:.25 for i in (ecodes.ABS_X, ecodes.ABS_Y, ecodes.ABS_RX)}
    curses.wrapper(mainLoop)


