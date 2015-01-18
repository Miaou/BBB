# -*- coding: utf-8 -*-
# Should be Python2/3 compatible


# The problem is that I did not foresee the fact that I would have variable hardware (new sensors)...
#  ... it is rather limited to do things with fixed number of sensors...

# So it should be moved to a greater structure, where each sensor could have a table...
# There would be a table (waveID, measureID, time), multiple tables (measureID, rawMeasure)
#  and a table (waveID, waveName) and a table (sensorName, tableName)...
# Maybe instead of sensors table, a generic (sensorID, measureID, rawMeasure) with a table (sensorID, sensorType, sensorName, exprRawToCelsius)
#  but be careful when being too generic...

# Sidenote about naming graphs: may not be such a good idea... maybe add a more "comment" system rather than referencing by name...

# The debate pro/con a single table having all measures is difficult.
# There could be a table per sensor, which leads to small and efficient tables (this is partitionning)
# Here are representative debates:
# http://stackoverflow.com/questions/22188846/sqlite-mysql-big-table-vs-multiple-small-tables
# http://sqlite.1065341.n5.nabble.com/Single-large-table-vs-several-smaller-tables-td78495.html
# http://dba.stackexchange.com/questions/56610/sqlite-design-better-to-have-many-tables-with-few-columns-or-few-tables-with-ma
# -> small tables is usually more "normalized" (only one version of the thruth), and more optimized for insert/access
# -> a large table avoids joins, but ... how to say that... they will be rare.
# -> small tables may be more confortable to work with (because it may be the way we imagine the data)
# -> a table is too large when it as several giga rows...

# So, the proposed scheme fot the tables:
# Sensors: sensorID PRIMARY, sensorPartNumber (manufacturing part number, e.g. "DS18B20"), sensorHardwareID BLOB (what we want if there is no HW id), exprRawToReadable
#  Sensors can be output too: command value of the fan speed for instance.
# Waves: waveID PRIMARY, timeStarted INTEGER, comment (long text (descr of the experiment) or nothing, not name, name is tedious and difficult to keep short)
#  Say, the waves IDs will now be AUTOINCREMENT instead of "random" integer: it will enforce the listing, even if it breaks multi-databaseS-wide indexing...
# SensorComment: sensorID FOREIGN, waveID FOREIGN, txtDescPlacement, txtPlotLegend
# Measures: waveID FOREIGN, time INTEGER (in secs), sensorID FOREIGN, rawValue INTEGER, PRIMARY KEY (waveID, time, sensorID)

# To do new measures: acquire a new waveID, optionnally leave a comment, select existing sensorsIDs, insert measures

# exprRawToReadable: an expression to be evaluated for each sensor to convert raw data to readable data (temperature, humidity, fan speed, ...),
#  should have only one local variable,
#  should be eval()-safe, so check it out, because it can be a source of code injection.
#  should tolerate the use of things like struct (?) maybe not, it would allow open(). So only struct ?

# The real problems will be with handling errors with being too hard on user.



import sqlite3
import time
pylab = None # These are representations, they may (should) move in another file
np = None
gnuplot = None
import subprocess # gnuplot
import os
import sys


# Handling compatibility for both Py2 and 3
#if sys.hexversion > 0x03000000:
# Print: sep=' ', end='\n', file=sys.stdout)
printme = lambda *args,**kwargs: kwargs.get('file',sys.stdout).write(kwargs.get('sep', ' ').join(args+(kwargs.get('end','\n'),)))



sDB='thermoLog.db'
exprRawToCelsiusMLX = 'raw*.02-273.15'
exprRawToCelsiusDS  = 'raw/16.'
class DAO(object):
    def __init__(self, sDB):
        self.sDB = sDB
        self.db = sqlite3.connect(self.sDB)
        self.db.execute('PRAGMA foreign_keys=1') # Enables the "foreign key" checking
        self.curWaveID = None
        with self.db as db:
            db.execute('CREATE TABLE IF NOT EXISTS Sensors (ID INTEGER PRIMARY KEY AUTOINCREMENT,\
                        bPartNumber BLOB NOT NULL, bHardID BLOB, exprRawToReadable TEXT)') # FIXME: avoid insertion of a (bPartNumber, bHardID) that already exists
            db.execute('CREATE TABLE IF NOT EXISTS Waves (ID INTEGER PRIMARY KEY AUTOINCREMENT,\
                        iTimeStarted INTEGER NOT NULL, sComment TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS SensorComments (SensorID INTEGER, WaveID INTEGER,\
                        sDescPlacement TEXT NOT NULL, sPlotLegend TEXT,\
                        FOREIGN KEY (SensorID) REFERENCES Sensors(ID),\
                        FOREIGN KEY (WaveID) REFERENCES Waves(ID),\
                        PRIMARY KEY (SensorID, WaveID))')
            db.execute('CREATE TABLE IF NOT EXISTS Measures (WaveID INTEGER, iTimeStamp INTEGER NOT NULL, SensorID INTEGER,\
                        iRawValue INTEGER,\
                        FOREIGN KEY (WaveID) REFERENCES Waves(ID),\
                        FOREIGN KEY (SensorID) REFERENCES Sensors(ID),\
                        PRIMARY KEY (WaveID, iTimeStamp, SensorID))')
    # -----
    #  API
    # -----
    # (to be completed)
    def newSensor(self, bPartNumber, bHardID=b'', exprRawToReadable=''):
        'Adds a sensor to the DB. Ignored if already exist'
        assert bPartNumber, "Please give the type of the sensor (e.g. the part number, DS18B20, ...)"
        with self.db as db:
            # FIXME: define behavior if sensor already exists (Exception? print? ...)
            if db.execute('SELECT ID FROM Sensors WHERE bPartNumber=? AND bHardID=?', (bPartNumber,bHardID)).fetchone():
                # FIXME: test me
                db.execute('UPDATE Sensors SET exprRawToReadable=? WHERE bPartNumber=? AND bHardID=?', (exprRawToReadable,bPartNumber,bHardID))
            else:
                db.execute('INSERT INTO Sensors(bPartNumber, bHardID, exprRawToReadable) VALUES(?,?,?)',
                           (bPartNumber, bHardID, exprRawToReadable))
    def iterSensors(self):
        'Returns an iterator on sensors (ID, bPartNumber, bHardwareID)\n(list(dao.iterSensors()) to obtain a list)'
        for tup in self.db.execute('SELECT * FROM Sensors'):
            yield tup
    def displaySensors(self):
        'Pretty print sensors list'
        # FIXME: Print will be made with fixed-width column to display things nicely.
        for ID, bPartN, bHardID, expr in self.iterSensors():
            print(ID, bPartN, bHardID, expr)
    def commentSensor(self, sensorID, sDescPlacement, sPlotLegend='', waveID=None):
        if not self.curWaveID and not waveID:
            raise ValueError('Could not guess which wave to comment')
        if not waveID:
            waveID = self.curWaveID
        with self.db as db:
            assert db.execute('SELECT ID FROM Sensors WHERE ID=?', (sensorID,)).fetchone(), "Sensor not yet in DB"
            assert db.execute('SELECT ID FROM Waves WHERE ID=?', (waveID,)).fetchone(), "Wave not yet in DB"
            db.execute('INSERT OR REPLACE INTO SensorComments VALUES(?,?,?,?)', (sensorID, waveID, sDescPlacement, sPlotLegend))

    def newWave(self, iTimeStamp=None, sComment=''):
        if not iTimeStamp:
            iTimeStamp = int(time.time())
        with self.db as db:
            cur = db.cursor()
            cur.execute('INSERT INTO Waves(iTimeStarted, sComment) VALUES(?,?)', (iTimeStamp, sComment))
            self.curWaveID = cur.lastrowid 
    def commentWave(self, sComment, waveID=None):
        if not self.curWaveID and not waveID:
            raise ValueError('Could not guess which wave to comment')
        if not waveID:
            waveID = self.curWaveID
        with self.db as db:
            assert db.execute('SELECT ID FROM Waves WHERE ID=?', (waveID,)).fetchone(), "Wave not yet in DB"
            db.execute('UPDATE Waves SET sComment=? WHERE ID=?', (sComment, sPlotLegend, waveID))
    def iterWaves(self):
        'Returns an iterator on waves (ID, iTimeStarted, sComment)'
        for tup in self.db.execute('SELECT * FROM Waves'):
            yield tup
    def displayWaves(self):
        'Future pretty print'
        # FIXME: pretty print
        for ID, iTime, sComm in self.iterWaves():
            print(ID, iTime, sComm)

    def newMeasure(self, sensorID, iRawValue, iTimeStamp=None, waveID=None):
        if not self.curWaveID and not waveID:
            raise ValueError('No current wave, did you forget to dao.newWave()?')
        if not waveID:
            waveID = self.curWaveID
        if not iTimeStamp:
            iTimeStamp = int(time.time())
        iTimeStamp = int(iTimeStamp)
        with self.db as db:
            # FIXME: define the 'measure already exists' behavior
            db.execute('INSERT OR REPLACE INTO Measures VALUES(?,?,?,?)', (waveID, iTimeStamp, sensorID, iRawValue))
    def iterMeasures(self, sensorID, waveID):
        'Iterates (iTimeStamp, fReadableValue) over Measures'
        with self.db as db:
            exprRaw, = db.execute('SELECT exprRawToReadable FROM Sensors WHERE ID=?', (sensorID,)).fetchone()
            print(exprRaw)
            for t,raw in db.execute('SELECT iTimeStamp,iRawValue FROM Measures WHERE WaveID=? AND SensorID=?', (waveID, sensorID)):
                yield (t, eval(exprRaw, {}, {'raw':raw}))
    
    # ---------
    #  old API
    # ---------
    # Still here to take some inspiration. Will be deleted.
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

    @staticmethod
    def assertPylab():
        global pylab, np
        if pylab and np:
            return True
        try:
            printme('Import pylab,numpy...', end='')
            import pylab
            import numpy as np
        except ImportError:
            printme(' Fail.\nPylab/numpy unavailable, sorry bro.')
            #printme('They are not available! Don\'t try to use DAODrawer again, please!')
            #del DAODrawer # FUCK YEAH (?)... but make DAODrawer global, otherwise it will be bound to a local variable that is not set yet.
            return False
        printme(' Ok')
        return True
    @staticmethod
    def assertGnuplot():
        global gnuplot
        if gnuplot:
            return True
        try:
            printme('Testing gnuplot...', end='')
            subprocess.call(['gnuplot', '-V'])
            gnuplot = True
        except OSError:
            printme(' Fail.\nGnuplot is not available from working directory, sorry bro.')
            return False
        printme(' Ok')
        return True
        
        

    def pylabByName(self, name):
        self._pylabPts(self.listEntriesByName(name), name)
    def pylabByIndex(self, i):
        self._pylabPts(self.listEntriesByIndex(i), 'n°{}'.format(i))
    def _pylabPts(self, lPts, name):
        if not DAODrawer.assertPylab():
            return
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
        if not DAODrawer.assertGnuplot():
            return
        f = open('tempgnu', 'wb')#, encoding='utf-8')
        f.write('set term dumb 180 50 \nset title "Jeu de température {}"\n'.format(name).encode())
        f.write("plot 'tempgnu' using 1:2 title 'TempCapteur' with lines, 'tempgnu' using 1:3 title 'TempSansContact' with dots\n\n".encode())
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










