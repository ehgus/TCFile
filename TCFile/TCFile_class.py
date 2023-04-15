from typing import Sequence
from PIL import Image
import numpy as np
import h5py

class TCFile(Sequence):
    '''
    interface class to TCF files.
    This class returns data as if list containg multiple data.
    Preview of the data is stored in attributes.
    * Note: It can read 3D, 2DMIP, BF. 

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
        elif '2DMIP' == imgtype or 'BF' == imgtype:
            dim = 2
        else:
            raise ValueError('The imgtype is not supported')

        with h5py.File(tcfname) as f:
            # validation of the given file
            if 'Data' not in f:
                raise ValueError('It is not tcf file')
            elif imgtype not in f['Data']:
                raise ValueError('The imgtype is not supported')
            # load attributes
            getAttr = lambda attrName: f[f'Data/{imgtype}'].attrs.get(attrName)[0]
        
            self.length = getAttr('DataCount')
            self.dataShape = list(getAttr(f'Size{axis}') for axis in  ('X', 'Y', 'Z')[:dim])
            self.dataShape.reverse()
            self.dataResolution = list(getAttr(f'Resolution{axis}') for axis in  ('X', 'Y', 'Z')[:dim])
            self.dataResolution.reverse()
            self.dt = f[f'Data/{imgtype}'].attrs.get('TimeInterval',default=[None])[0]
            if self.dt is None:
                self.dt = 0
        
        self.tcfname = tcfname
        self.imgtype = imgtype
    
    def __getitem__ (self, key:int) -> np.ndarray:
        '''
        Return
        ------
        data : numpy.ndarray[uint8]
            return a single image.
            When choosing 2DMIP or 3D data as a output, it returns refractive index map,
            and a RGB image for bright field image.

        Raises
        ------
        TypeError
            If key is not int
        IndexError
            If key is out of bound
        '''
        length = len(self)
        if not isinstance(key, int):
            raise TypeError(f'{self.__class__} indices must be integer, not {type(key)}')
        if key < -length or key >= length:
            raise IndexError(f'{self.__class__} index out of range')
        key = (key + length) % length

        with h5py.File(self.tcfname) as f:
            data = f[f'Data/{self.imgtype}/{key:06d}'][()]
        
        if ('3D' == self.imgtype or '2DMIP' == self.imgtype) and not np.issubdtype(data.dtype, np.floating):
            # To preserve the storage, some TCF file save data as a UInt16 integer scaled by 1e4
            data = data.astype(np.float32)
            data /= 1e4
        elif 'BF' == self.imgtype:
            data = Image.fromarray(data, mode = 'RGB')

        return data

    def __len__(self):
        '''
        Return the number of images available. 
        '''
        return self.length

