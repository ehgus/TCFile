from typing import List, Union
from enum import Enum
from collections.abc import Sequence, MutableMapping
import h5py
import numpy as np
from multimethod import multimethod

class _ImageDimension(Enum):
    '''
    image dimension
    '''
    TWO_D = 2
    THREE_D = 3

    def integer(self):
        '''
        return corresponding integer value
        '''
        return self.value

    def string(self):
        '''
        return corresponding string value
        '''
        return str(self.value)+'D'

class _BasicTCFile(Sequence):
    '''
    Basic interface class to TCF files.
    This class returns data as if list containg multiple data.
    Preview of the data is stored in attributes.

    Attributes
    ----------
    length : int
        time series length of the TCF file
    shape : numpy.array[int]
        shape of single shot data
    resol : numpy.array[float]
        (unit: μm) resolution of data. It represents unit resolution per pixel
    dt : float
        (unit: s) Time steps of data. Zero if it is single shot data
    '''
    # It is not intended to be used for users directly.

    def __init__(self, tcfname:str, dim:int):
        '''
        Paramters
        ---------
        tcfname : str
            location of the target TCF file
        dim : Union[int,_ImageDimension]
            image type to see. Either 2 or 3 is the only option.

        Raises
        ------
        ValueError
            If dim is unsupported given tcf file.
        '''
        self.tcfname=tcfname
        if isinstance(dim, _ImageDimension):
            self.dim=dim
        elif dim in map(lambda x: x.integer(), _ImageDimension.__members__.values()):
            self.dim=_ImageDimension(dim)
        else:
            raise ValueError('dim only support "2D" and "3D"')
        _idx = -self.dim.integer()
        with h5py.File(tcfname) as f:
            if self.dim.string() not in f['Data']:
                raise ValueError('The TCFile does not support the suggested image type')
            getAttr = lambda attrName: f[f'Data/{self.dim.string()}'].attrs[attrName][0]
            self.length = getAttr('DataCount')
            self.shape = tuple(getAttr(f'Size{axis}') for axis in  ('Z', 'Y', 'X')[_idx:])
            self.resol = tuple(getAttr(f'Resolution{axis}') for axis in  ('Z', 'Y', 'X')[_idx:])
            self.dt = 0 if self.length == 1 else getAttr('TimeInterval')

    def __getitem__(self, key: int) -> np.ndarray:
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

        with h5py.File(self.tcfname) as f:
            if key < 0:
                key += self.length
            data = f[f'Data/{self.dim.string()}/{key:06d}'][()]
        return data

    def __len__(self):
        return self.length

class TCFile(_BasicTCFile):
    '''
    Basic interface class to TCF files.
    This class returns data as if list containg multiple data.
    Preview of the data is stored in attributes.

    Attributes
    ----------
    length : int
        time series length of the TCF file
    shape : numpy.array[int]
        shape of single shot data
    resol : numpy.array[float]
        (unit: μm) resolution of data. It represents unit resolution per pixel
    dt : float
        (unit: s) Time steps of data. Zero if it is single shot data
    dtype : float
        return type of refractive index data
    '''

    def __init__(self, tcfname:str, dim:Union[int,_ImageDimension], dtype=np.float32):
        '''
        Paramters
        ---------
        tcfname : str
            location of the target TCF file
        dim : Union[int,_ImageDimension]
            image type to see. Either '2D' or '3D' is the only option.
        dtype : float (default: numpy.float32)
            return type of refractive index data

        Raises
        ------
        ValueError
            If dim is unsupported given tcf file.
        '''
        super().__init__(tcfname, dim)
        self.dtype = dtype

    def get_raw(self, key: int) -> np.ndarray:
        '''
        Return raw data.
        raw data size is half of real refractive index data.
        Therefore, the raw data might be useful when planning image processing only.

        Parameters
        ----------
        key: int
            index of data
        '''
        return super().__getitem__(key)

    def __getitem__ (self, key) -> np.ndarray:
        '''
        Return refractive index data.

        Parameters
        ----------
        key: int
            index of data
        '''
        data = self.get_raw(key).astype(self.dtype)
        data /= 1e4 # see _BasicTCFile.__getitem__ to know the meaning of this line
        return data



class _BasicTCFcell(MutableMapping):
    '''
    It contains only data, not attributes

    Attributes
    ----------
    properties : dict
        properties given cell type
    '''
    @multimethod
    def __init__(self, properties:dict):
        self.properties = properties

    @multimethod
    def __init__(self, f:h5py._hl.group.Group):
        self.properties = {}
        for key in f.keys():
            self[key] = f[key][()]

    def __getitem__(self, key:str):
        return self.properties[key]

    def __setitem__(self, key:str, item):
        self.properties[key] = item

    def __delitem__(self, key:str):
        del self.properties[key]

    def __iter__(self):
        return iter(self.properties)

    def __len__(self):
        return len(self.properties)

    def save(self, io):
        for key in self.keys():
            io.create_dataset(key, data = self[key])

class TCFcell(_BasicTCFcell):
    '''
    '''

    @multimethod
    def __init__(self, tcfile:TCFile, idx:int, properties = {}, **kwargs):
        properties.update(**kwargs)
        super().__init__(properties)
        # attributes
        self.tcfname = tcfile.tcfname
        self.resol = tcfile.resol
        self.dim = tcfile.dim
        self.idx = idx

    @multimethod
    def __init__(self, fname:str):
        with h5py.File(fname,'r') as f:
            if  'type' in f.attrs.keys() and f.attrs['type'] == 'TCFcell':
                super().__init__(f['/'])
                # get attributes
                self.tcfname = f.attrs['tcfname']
                self.idx = f.attrs['idx']
                self.resol = f.attrs['resol']
                self.dim = _ImageDimension(f.attrs['dim'])
            else:
                NameError('The file does not support TCFcell')

    def save(self, fname:str):
        with h5py.File(fname,'w') as f:
            super().save(f)
            # set attributes
            f.attrs['type'] = 'TCFcell'
            f.attrs['tcfname'] = self.tcfname
            f.attrs['idx'] = self.idx
            f.attrs['resol'] = self.resol
            f.attrs['dim'] = self.dim.value

class TCFcell_t:

    @multimethod
    def __init__(self, tcfcells:List[TCFcell]):
        '''
        validation
        - each tcfcells comes from the same tcfile with incrementing index (TODO)
        '''

        self.tcfcells = [_BasicTCFcell(tcfcell.properties) if tcfcell is not None else None for tcfcell in tcfcells]
        self.tcfname = tcfcells[0].tcfname
        self.dim = tcfcells[0].dim
        self.len = len(TCFile(self.tcfname, self.dim.value))

    @multimethod
    def __init__(self, fname:str):
        with h5py.File(fname,'r') as f:
            if f.attrs["type"] == 'TCFcell_t':
                self.tcfname = f.attrs['tcfname']
                length = f.attrs['len']
                self.tcfcells = [None] * length
                for ind in f.keys():
                    i = int(ind)
                    self.tcfcells[i] = _BasicTCFcell(f[ind])
            else:
                NameError('The file does not support TCFcell_t')

    def __getitem__(self, key:int) -> TCFcell:
        return self.tcfcells[key]

    def __setitem__(self, key:int, item:TCFcell):
        self.tcfcells[key] = item

    def append(self,item:Union[TCFcell,None]):
        self.tcfcells.append(item)

    def extend(self,items:List[Union[TCFcell,None]]):
        self.tcfcells.extend(items)

    def __len__(self) -> int:
        return len(self.tcfcells)

    def save(self, fname:str):
        with h5py.File(fname,'w') as f:
            f.attrs['type'] = 'TCFcell_t'
            f.attrs['tcfname'] = self.tcfname
            f.attrs['len'] = len(self)
            for (i,tcfcell) in enumerate(self.tcfcells):
                if tcfcell is None:
                    continue
                grp =f.create_group(f'{i:06d}')
                for key in tcfcell.keys():
                    grp.create_dataset(key, data = tcfcell[key])
