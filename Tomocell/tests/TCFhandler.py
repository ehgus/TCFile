from . import TCFile, TCFcell, TCFcell_t
import numpy as np
import os

fname = f"{os.path.dirname(__file__)}/test_snapshot.TCF"

class TestTCFile:

    def test_creation(self):
        self.tcfile3d = TCFile(fname,'3D')
        self.tcfile2d = TCFile(fname,'2D')
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
    

    