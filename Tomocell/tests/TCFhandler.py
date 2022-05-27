from . import TCFile, TCFcell, TCFcell_t
import numpy as np
import os
import tempfile

fname = f"{os.path.dirname(__file__)}/test_snapshot.TCF"

class TestTCFile:

    def test_creation(self):
        TCFile(fname,'3D')
        try:
            TCFile(fname,'4D')
        except ValueError as e:
            if e.args[0] != 'The imgtype is not supported':
                assert False
    
    def test_read(self):
        tcfile = TCFile(fname,'3D')
        data =tcfile[0]
        assert np.min(data) > 1     #physically true
    
    def test_iterative_read(self):
        tcfile = TCFile(fname,'3D')
        for data in tcfile:
            assert np.array_equal(tcfile.dataShape, data.shape)
            
    def test_attributes(self):
        tcfile = TCFile(fname,'3D')
        data = tcfile[0]
        assert np.array_equal(tcfile.dataShape, data.shape)
        assert len(tcfile) == 1
        assert tcfile.dt == 0
    
class TestTCFcell:

    def test_creation(self):
        tcfile = TCFile(fname, '3D')
        tcfcell = TCFcell(tcfile, 0, DMass = 80,CMass = (1.0,1.0,1.0), Vol = 3)
        #y = TCFcell(tcfile, 0, dict(CMass = (1.0,1.0,1.0), Vol = 3, DMass = 80))
        #z = TCFcell(tcfile, 0, dict(CMass = (1.0,1.0,1.0)), Vol = 3, DMass = 80)

        assert np.array_equal(tcfcell['CMass'], (1.0,1.0,1.0))
        assert tcfcell['Vol'] == 3
        assert tcfcell['DMass'] == 80
        try:
            tcfcell['hello world']
        except KeyError:
            pass

    def test_save_load(self):
        tcfile = TCFile(fname, '3D')
        tcfcell = TCFcell(tcfile, 0, DMass = 80,CMass = (1.0,1.0,1.0), Vol = 3)
        #save
        tmpf = tempfile.TemporaryFile()
        tmpf.close()
        tcfcell_fname = tmpf.name
        tcfcell.save(tcfcell_fname)
        #load
        loaded_tcfcell= TCFcell(tcfcell_fname)

        for key in ('CMass','DMass','Vol'):
            loaded_tcfcell.CMass
            loaded_val = loaded_tcfcell[key]
            ref_val = tcfcell[key]
            try:
                assert loaded_val == ref_val
            except ValueError:
                assert np.array_equal(loaded_val, ref_val)