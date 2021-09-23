from . import TCFile, TCFcell, TCFcell_t
import numpy as np
import os
import tempfile

fname = f"{os.path.dirname(__file__)}/test_snapshot.TCF"

class TestTCFile:

    def test_creation(self):
        TCFile(fname,'3D')
        TCFile(fname,'2D')
        try:
            TCFile(fname,'4D')
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
        x = TCFcell(tcfile, 0, CM = (1.0,1.0,1.0), volume = 3, drymass = 80)
        y = TCFcell(tcfile, 0, dict(CM = (1.0,1.0,1.0), volume = 3, drymass = 80))
        z = TCFcell(tcfile, 0, dict(CM = (1.0,1.0,1.0)), volume = 3, drymass = 80)

        assert np.array_equal(x['CM'], (1.0,1.0,1.0))
        assert x['volume'] == 3
        assert x['drymass'] == 80
        try:
            x['hello world']
        except KeyError:
            pass 
        assert x.properties == y.properties == z.properties

    def test_save_load(self):
        tcfile = TCFile(fname, '3D')
        tcfcell = TCFcell(tcfile, 0, CM = np.array((1.0,1.0,1.0)), volume = 3, drymass = 80)
        #save
        tmpf = tempfile.TemporaryFile()
        tmpf.close()
        tcfcell_fname = tmpf.name
        tcfcell.save(tcfcell_fname)
        #load
        loaded_tcfcell= TCFcell(tcfcell_fname)

        for key,val in loaded_tcfcell.items():
            try:
                assert val == tcfcell[key]
            except ValueError:
                assert np.array_equal(val, tcfcell[key])