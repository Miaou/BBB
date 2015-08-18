#!/usr/bin/python3
#

from curses import wrapper
import curses
import time
import random



def test(stdscr):
    print('{}x{}'.format(curses.LINES,curses.COLS))
    #return
    stdscr.clear()
    stdscr.scrollok(True)
    for i in range(100):
        stdscr.addstr(curses.LINES-1,0,'{:03d}'.format(i))
        stdscr.scroll(1)
        stdscr.refresh()

def test2(stdscr):
    for i in range(100):
        stdscr.move(0,0)
        #stdscr.clrtoeol()
        #stdscr.clear() # Flickers
        stdscr.erase()
        stdscr.addstr('{:03d}x{:03d}\n'.format(*stdscr.getmaxyx()))
        stdscr.addstr('{:03d}\n'.format(i))
        stdscr.refresh()
        time.sleep(1)

def pileHigher(stdscr):
    lH = [0]*15
    lTgt = [random.randint(2,8) for i in lH]
    bEnd = False
    iH = 0
    chlast = None
    stdscr.nodelay(True)
    stdscr.addstr(0,0,'--- PILE HIGHER ---')
    while not bEnd:
        for i,t in enumerate(lTgt):
            stdscr.addch(1, 2*i, '{}'.format(t), lH[i]==t and (curses.A_BOLD|curses.A_UNDERLINE) or curses.A_NORMAL)
        stdscr.move(12,iH)
        ch = stdscr.getch()
        if ch == chlast:
            continue
        elif ch == curses.KEY_LEFT:
            if iH > 0:
                iH -= 1
        elif ch == curses.KEY_RIGHT:
            if iH < len(lH)-1:
                iH += 1
        elif ch == curses.KEY_UP:
            if lH[iH] < 10:
                lH[iH] += 1
            stdscr.chgat(12-lH[iH],iH,1,curses.A_REVERSE)
        elif ch == curses.KEY_DOWN:
            stdscr.chgat(12-lH[iH],iH,1,curses.A_NORMAL)
            if lH[iH] > 0:
                lH[iH] -= 1
        elif ch in (ord('q'),ord('Q')):
            bEnd = True
        chlast = ch
        time.sleep(.01) 



wrapper(pileHigher)


