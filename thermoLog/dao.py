#
# -*- coding: utf-8 -*-
# Python2/3 compatible

# Index-based access functions are ... bad. It relies on the fact that a given row in the database is
#  always accessed the same, so that it's index is always the same...

# The problem is that I did not foresee the fact that I would have variable (enlarging) hardware...
#  ... it is rather limited to do things with fixed number of sensors...

# So it should be moved to a greater structure, where each sensor could have a table
# There would be a table (waveID, measureID, time), multiple tables (measureID, rawMeasure)
#  and a table (waveID, waveName) and a table (sensorName, tableName)...
# Maybe instead of sensors table, a generic (sensorID, measureID, rawMeasure) with a table (sensorID, sensorType, sensorName)
#  but be careful when being too generic...

# Note about naming graphs: may not be such a good idea... maybe add a more "comment" system rather than referencing by name...

# http://stackoverflow.com/questions/22188846/sqlite-mysql-big-table-vs-multiple-small-tables



import sqlite3
import time
pylab = None
np = None
import subprocess # gnuplot
import os
import sys


# Handling compatibility for both Py2 and 3
#if sys.hexversion > 0x03000000:
#    printme = lambda *args,**kwargs: print(*args, **kwargs)
#else:
printme = lambda *args,**kwargs: sys.stdout.write(' '.join(args+('\n',))) # Should analyze kwargs, and search for sep, end, ...
#if sys.hexversion < 0x03000000:
#    from io import open


sDB='thermoLog.db'
class DAO(object):
    #RAW_TO_CELSIUS = lambda i:i*.02-273.15 # Python3-style
    @staticmethod
    def RAW_TO_CELSIUS(i):
        return i*.02-273.15

    def __init__(self, sDB, curWave=None):
        self.sDB = sDB
        self.db = sqlite3.connect(self.sDB)
        self.db.execute('PRAGMA foreign_keys=1')
        if curWave == None:
            curWave=int(time.time())
        self.curWave = curWave
        with self.db as db:
            db.execute('CREATE TABLE IF NOT EXISTS logThermo (wave INTEGER, time INTEGER,\
                        iTempAmb INTEGER, iTempObj INTEGER, PRIMARY KEY(wave,time));')
            db.execute('CREATE TABLE IF NOT EXISTS waveNames (wave INTEGER, name TEXT PRIMARY KEY);')#,\
                        #FOREIGN KEY (wave) REFERENCES logThermo(wave));') # Design flaw: the foreign key must match a primary key (!!!) ("lol")

    def newEntry(self, fTime, iRawTempA, iRawTempO):
        with self.db as db:
            db.execute('INSERT INTO logThermo VALUES(?,?,?,?)', (self.curWave, int(fTime), iRawTempA, iRawTempO))

    def nameCurrWave(self, name):
        self.nameWave(self.curWave, name)
    def nameWave(self, wave, name):
        with self.db as db:
            n, = db.execute('SELECT count(*) FROM logThermo WHERE wave=?', (wave,)).fetchone()
            if not n:
                print('DAO.nameWave: no such wave {}'.format(wave))
                return
            n, = db.execute('SELECT count(*) FROM waveNames WHERE name=?', (name,)).fetchone()
            if n:
                print('DAO.nameWave: name "{}" already given'.format(name))
                return
            db.execute('INSERT OR REPLACE INTO waveNames VALUES(?,?)', (wave, name))
    def nameWaveByIndex(self, i, name):
        self.nameWave(self._listWaves()[i], name)
    
    def _listWaves(self):
        return [wave for wave, in self.db.execute('SELECT DISTINCT wave FROM logThermo')]
    def listEntriesByWave(self, wave):
        return [(t,DAO.RAW_TO_CELSIUS(a),DAO.RAW_TO_CELSIUS(b)) for t,a,b in
                self.db.execute('SELECT time,iTempAmb,iTempObj FROM logThermo WHERE wave=?', (wave,))]
    def listEntriesByName(self, name):
        n, = self.db.execute('SELECT count(*) FROM waveNames WHERE name=?', (name,)).fetchone()
        if not n:
            print('DAO.listEntriesByName: no such wave named "{}"'.format(name))
        wave, = self.db.execute('SELECT wave FROM waveNames WHERE name=?', (name,)).fetchone()
        return self.listEntriesByWave(wave)
    def listEntriesByIndex(self, i):
        return self.listEntriesByWave(self._listWaves()[i])
    def listCurrEntries(self):
        return self.listEntriesWave(self.curWave)

    #def showWaves(self):
    #    for i,wave in enumerate(self.listWaves()):
    #        print('{:>3d} @ {},  {} samples'.format(i, time.ctime(wave),
    #                                        self.db.execute('SELECT count(time) FROM logThermo WHERE wave=?', (wave,)).fetchone()[0]))
    #def showWavesNames(self):
    def showWaves(self):
        lWN = list(self.db.execute('SELECT DISTINCT name, wave, count(time)\
                                    FROM logThermo LEFT JOIN waveNames USING (wave)\
                                    GROUP BY wave;'))
        lenMaxName = max( len(max(lWN, key=lambda t:t[0] or '')[0] or '')+1, len(str(len(lWN)))+2 )
        for i,(waveN,wave,cnt) in enumerate(lWN):
            if waveN:
                print('{:>{}} @ {},  {} samples'.format(waveN, lenMaxName, time.ctime(wave), cnt))
            else:
                print('# {:>{}} @ {},  {} samples'.format(i, lenMaxName-2, time.ctime(wave), cnt))



# Any name but DAODrawer works with super()... That smells like a bug.
# No. The bug is that del DAODraws is executed while parsing...
class DAODrawer(DAO):
    def __init__(self, sDB, curWave=None):
        global pylab, np
        super(DAODrawer,self).__init__(sDB, curWave)
        #super().__init__(sDB, curWave)
        if not pylab:
            printme('Import pylab,numpy...', end='')
            try:
                import pylab
                import numpy as np
            except ImportError:
                printme('They are not available! Don\'t try to use DAODrawer again, please!')
                #del DAODrawer # FUCK YEAH (?)
                del self # Useless, because only the reference "self" to the object is destroyed ^^
                return
            printme(' Ok')

    def pylabByName(self, name):
        self._pylabPts(self.listEntriesByName(name), name)
    def pylabByIndex(self, i):
        self._pylabPts(self.listEntriesByIndex(i), 'n°{}'.format(i))
    def _pylabPts(self, lPts, name):
        a,b,c = list(zip(*lPts))
        a = np.array(a)-a[0]
        pylab.plot(a,b)
        pylab.plot(a,c)
        pylab.legend( ('Température du capteur (°C)', 'Température mesurée de l\'objet distant (°C)') )
        pylab.xlabel('Temps (s)')
        pylab.ylabel('Température (°C)')
        pylab.title('Jeu de température {}'.format(name))
        pylab.show()

    def gnuplotByName(self, name):
        self._gnuplotPts(self.listEntriesByName(name), name)
    def gnuplotByIndex(self, i):
        self._gnuplotPts(self.listEntriesByIndex(i), 'n°{}'.format(i))
    def _gnuplotPts(self, lPts, name):
        f = open('tempgnu', 'wb')#, encoding='utf-8')
        f.write(b'set term dumb 180 50 \nset title "Jeu de température {}"\n'.format(name))
        f.write(b"plot 'tempgnu' using 1:2 title 'TempCapteur' with lines, 'tempgnu' using 1:3 title 'TempSansContact' with dots\n\n")
        for x,y,z in lPts:
           f.write(b"{:.02f} {:.02f} {:.02f}\n".format(x-lPts[0][0],y,z))
        f.write(b"e\n")
        f.close()
        gnuplot = subprocess.Popen(["gnuplot","tempgnu"],
                           stdout=subprocess.PIPE)
        txt = gnuplot.communicate()[0]
        os.remove('tempgnu')
        print(txt.decode('utf-8'))



if __name__=='__main__':
    print('DAO().showWaves()')
    print('import pylab')

if False:
    import pylab
    import numpy as np
    lPts = DAO().listEntriesWave(DAO().listWaves()[1])
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
    f.write("plot 'tempgnu' using 1:2 title 'TempCapteur' with lines, 'tempgnu' using 1:3 title 'TempSansContact' with lines\n\n")
    for x,y,z in lPts:
       f.write("{:.02f} {:.02f} {:.02f}\n".format(x-lPts[0][0],y,z))
    f.write("e\n")
    f.close()
    gnuplot = subprocess.Popen(["gnuplot","tempgnu"],
                       stdout=subprocess.PIPE)
    txt = gnuplot.communicate()[0]
    os.remove('tempgnu')
    print(txt.decode())







