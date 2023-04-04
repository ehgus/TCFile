import sys
import os
sys.path.insert(0, os.path. os.path.dirname(os.path.abspath(os.path.realpath('__file__'))))

from TCFile import TCFile
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
        assert np.array_equal(tcfile.dataShape, data.shape)
    
    def test_iterative_read(self):
        tcfile = TCFile(fname,'3D')
        for data in tcfile:
            assert np.array_equal(tcfile.dataShape, data.shape)
            
    def test_attributes(self):
        tcfile = TCFile(fname,'3D')
        assert len(tcfile) == 10
        assert tcfile.dt >= 0
