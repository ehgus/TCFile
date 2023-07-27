from . import SAMPLE_TCF_FILE
from TCFile import TCFile
import numpy as np

class TestTCFile:

    def test_creation(self):
        TCFile(SAMPLE_TCF_FILE,'3D')
        try:
            TCFile(SAMPLE_TCF_FILE,'4D')
        except ValueError as e:
            if e.args[0] != 'The imgtype is not supported':
                raise e
    
    def test_read(self):
        tcfile = TCFile(SAMPLE_TCF_FILE,'3D')
        data =tcfile[0]
        assert np.array_equal(tcfile.data_shape, data.shape)
    
    def test_iterative_read(self):
        tcfile = TCFile(SAMPLE_TCF_FILE,'3D')
        for data in tcfile:
            assert np.array_equal(tcfile.data_shape, data.shape)
            
    def test_attributes(self):
        tcfile = TCFile(SAMPLE_TCF_FILE,'3D')
        assert len(tcfile) == 10
        assert tcfile.dt >= 0
