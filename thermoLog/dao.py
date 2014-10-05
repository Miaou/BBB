#
# -*- coding: utf-8 -*-
# Python2/3 compatible


import sqlite3
import time


class DAO:
    #RAW_TO_CELSIUS = lambda i:i*.02-273.15 # Python3-style
    @staticmethod
    def RAW_TO_CELSIUS(i):
        return i*.02-273.15

    def __init__(self, sDB='thermoLog.db', curWave=int(time.time())):
        self.sDB = sDB
        self.db = sqlite3.connect(self.sDB)
        self.curWave = curWave
        with self.db as db:
            db.execute('CREATE TABLE IF NOT EXISTS logThermo(wave INTEGER, time INTEGER,\
                        iTempAmb INTEGER, iTempObj INTEGER, PRIMARY KEY(wave,time));')

    def newEntry(self, fTime, iRawTempA, iRawTempO):
        with self.db as db:
            db.execute('INSERT INTO logThermo VALUES(?,?,?,?)', (self.curWave, int(fTime), iRawTempA, iRawTempO))
    
    def listWaves(self):
        return [wave for wave, in self.db.execute('SELECT DISTINCT wave FROM logThermo')]
    def listEntriesWave(self, wave):
        return [(t,DAO.RAW_TO_CELSIUS(a),DAO.RAW_TO_CELSIUS(b)) for t,a,b in self.db.execute('SELECT time,iTempAmb,iTempObj FROM logThermo WHERE wave=?', (wave,))]
    def listEntries(self):
        return self.listEntriesWave(self.curWave)

    def showWaves(self):
        for i,wave in enumerate(self.listWaves()):
            print('{:>3d} @ {},  {} samples'.format(i, time.ctime(wave), self.db.execute('SELECT count(time) FROM logThermo WHERE wave=?', (wave,)).fetchone()[0]))




if __name__=='__main__':
    print('DAO().showWaves()')
    print('import pylab')
    
    import pylab
    import numpy as np
    lPts = DAO().listEntriesWave(DAO().listWaves()[0])
    a,b,c = list(zip(*lPts))
    a = np.array(a)-a[0]
    pylab.plot(a,b)
    pylab.plot(a,c)
    pylab.legend( ('Température du capteur (°C)', 'Température mesurée de l\'objet distant (°C)') )
    pylab.xlabel('Temps (s)')
    pylab.ylabel('Température (°C)')
    pylab.title('Températures de ma pièce')
    pylab.show()

    # http://stackoverflow.com/questions/20295646/python-ascii-plots-in-terminal
    # Sadly, gnuplot on stdin is more complex to manipulate (http://stackoverflow.com/questions/4981279/how-to-make-several-plots-from-the-same-standard-input-data-in-gnuplot)
    import subprocess
    import os
    f = open('tempgnu', 'w')
    f.write("set term dumb 180 50 \n")
    f.write("plot 'tempgnu' using 1:2 title 'TempCapteur' with linespoints, 'tempgnu' using 1:3 title 'TempSansContact' with linespoints\n\n")
    for x,y,z in lPts:
       f.write("{:.02f} {:.02f} {:.02f}\n".format(x-lPts[0][0],y,z))
    f.write("e\n")
    f.close()
    gnuplot = subprocess.Popen(["gnuplot","tempgnu"],
                       stdout=subprocess.PIPE)
    txt = gnuplot.communicate()[0]
    os.remove('tempgnu')
    print(txt.decode())







