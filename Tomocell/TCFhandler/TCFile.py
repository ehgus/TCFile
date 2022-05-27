from typing import Sequence
import numpy as np
import h5py

class TCFile(Sequence):
    '''
    interface class to TCF files.
    This class returns data as if list containg multiple data.
    Preview of the data is stored in attributes.
    * Note: It can only read 2D, 3D for now. (No fluorence file)

    Attributes
    ----------
    length : int
        time series length of the TCF file
    dataShape : numpy.array[int]
        shape of single shot data
    dataResolution : numpy.array[float]
        (unit: μm) resolution of data. It represents unit resolution per pixel
    dt : float
        (unit: s) Time steps of data. Zero if it is single shot data
    tcfname : str
    imgtype : str
    '''

    def __init__(self, tcfname:str, imgtype:str):
        '''
        Paramters
        ---------
        tcfname : str
            location of the target TCF file
        imgtype : str
            image type to see

        Raises
        ------
        ValueError
            If imgtype is unsupported given tcf file.
        '''
        # validation of input parameters
        if '3D' == imgtype:
            dim = 3
        else:
            raise ValueError('The imgtype is not supported')

        with h5py.File(tcfname) as f:
            # validation of the given file
            if 'Data' not in f:
                raise ValueError('It is not tcf file')
            elif imgtype not in f['Data']:
                raise ValueError('The imgtype is not supported')
            # load attributes
            getAttr = lambda attrName: f[f'Data/{imgtype}'].attrs[attrName][0]
        
            self.length = getAttr('DataCount')
            self.dataShape = list(getAttr(f'Size{axis}') for axis in  ('X', 'Y', 'Z')[:dim])
            self.dataShape.reverse()
            self.dataResolution = list(getAttr(f'Resolution{axis}') for axis in  ('X', 'Y', 'Z')[:dim])
            self.dataResolution.reverse()
            self.dt = 0 if self.length == 1 else getAttr('TimeInterval')
        
        self.tcfname = tcfname
        self.imgtype = imgtype
    
    def __getitem__ (self, key:int) -> np.ndarray:
        '''
        Return
        ------
        data : numpy.ndarray[uint8]
            raw data of refractive index mutliplided by 1e4.

        Raises
        ------
        TypeError
            If key is not int
        IndexError
            If key is out of bound
        '''
        if not isinstance(key, int):
            raise TypeError(f'{self.__class__} indices must be integer, not {type(key)}')
        if key < -self.length or key >= self.length:
            raise IndexError(f'{self.__class__} index out of range')
        key = (key + self.length) % self.length

        with h5py.File(self.tcfname) as f:
            data = f[f'Data/{self.imgtype}/{key:06d}'][()] 
        
        if not np.issubdtype(data.dtype, np.floating):
            # To preserve the storage, some TCF file save data as a integer scaled by 1e4
            data = data.astype(np.float32)
            data /= 1e4

        return data

    def __len__(self):
        return self.length

