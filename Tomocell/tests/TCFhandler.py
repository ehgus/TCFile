from . import TCFile
import numpy as np
import os

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
