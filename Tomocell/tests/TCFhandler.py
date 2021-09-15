from . import TCFile, TCFcell, TCFcell_t
import numpy as np
import os
import pytest
import tempfile

fname = f"{os.path.dirname(__file__)}/test_snapshot.TCF"

class TestTCFile:

    def test_creation(self):
        TCFile(fname,'3D')
        TCFile(fname,'2D')
        try:
            FourD = TCFile(fname,'4D')
        except ValueError as e:
            if e.args[0] != 'imgtype only support "2D" and "3D"':
                assert False
    
    def test_read(self):
        tcfile = TCFile(fname,'3D')
        data =tcfile[0]
        assert np.min(data) > 1     #physically true
    
    def test_iterative_read(self):
        tcfile = TCFile(fname,'3D')
        for data in tcfile:
            assert tcfile.shape == data.shape
            
    def test_attributes(self):
        tcfile = TCFile(fname,'3D')
        data = tcfile[0]
        assert tcfile.shape == data.shape
        assert len(tcfile) == 1
        assert tcfile.dt == 0
    
class TestTCFcell:

    def test_creation(self):
        tcfile = TCFile(fname, '3D')
        x = TCFcell(tcfile, 0, CM =  (1.0,1.0,1.0), volume = 3, drymass = 80)
        y = TCFcell(tcfile, 0, dict(CM =  (1.0,1.0,1.0), volume = 3, drymass = 80))
        z = TCFcell(tcfile, 0, dict(CM =  (1.0,1.0,1.0)), volume = 3, drymass = 80)

        assert x['CM'] == (1.0,1.0,1.0)
        assert x['volume'] == 3
        assert x['drymass'] == 80
        try:
            x['hello world']
        except KeyError:
            pass 
        assert x.properties == y.properties == z.properties

    def test_save_load(self):
        tcfile = TCFile(fname, '3D')
        tcfcell = TCFcell(tcfile, 0, CM =  (1.0,1.0,1.0), volume = 3, drymass = 80)
        #save
        tmpf = tempfile.TemporaryFile()
        tmpf.close()
        tcfcell_fname = tmpf.name
        tcfcell.save(tcfcell_fname)
        #load
        loaded_tcfcell= TCFcell(tcfcell_fname)
        raise ValueError(loaded_tcfcell.properties)
        assert tcfcell.properties == loaded_tcfcell.properties

    def test_load(self):
        pass
    
    def test_attributes(self):
        pass

class TestTCFcell_t:

    def test_creation(self):
        pass

    def test_read(self):
        pass
    
    def test_iterative_read(self):
        pass

    def test_save(self):
        pass

    def test_load(self):
        pass
    
    def test_attributes(self):
        pass