import h5py
import numpy as np
from typing import List, Union
from multimethod import multimethod
from enum import Enum

class _ImgDim(Enum):
    TwoD = '2D'
    ThreeD = '3D'
    
    def intval(self) -> int:
        if self is _ImgDim.TwoD:
            return 2
        else:
            return 3

class _BasicTCFile:

    def __init__(self, tcfname:str, imgtype:str):
            self.tcfname=tcfname
            if imgtype in _ImgDim._value2member_map_.keys():
                self.imgtype=_ImgDim(imgtype)
            else:
                raise ValueError('imgtype only support "2D" and "3D"')
            _idx = -self.imgtype.intval()

            with h5py.File(tcfname) as f:
                if imgtype not in f['Data']:
                    raise ValueError('The TCFile does not support the suggested image type')
                getAttr = lambda name: f[f'Data/{imgtype}'].attrs[name][0]
                self.length = getAttr('DataCount')
                self.shape = tuple(getAttr(f'Size{idx}') for idx in  ('Z', 'Y', 'X')[_idx:])
                self.resol = tuple(getAttr(f'Resolution{idx}') for idx in  ('Z', 'Y', 'X')[_idx:])
                self.Volpix = np.prod(self.resol) # (μm)^D (D:dimensions)
                self.dt = 0 if self.length == 1 else getAttr('TimeInterval') # s
        
    def __getitem__(self, key):
        if key >= self.length:
            raise IndexError(f'{TCFile.__name__} index out of range')
        with h5py.File(self.tcfname) as f:
            data = f[f'Data/{self.imgtype.value}/{key:06d}'][()]
        return data
    
    def __len__(self):
        return self.length

class TCFile(_BasicTCFile):

    def __init__(self, tcfname:str, imgtype:str, dtype=np.float32):
        super().__init__(tcfname, imgtype)
        self.dtype = dtype
    
    def getrawdata(self, key) -> np.ndarray:
        return super().__getitem__(key)

    def __getitem__ (self, key) -> np.ndarray:
        data = self.getrawdata(key).astype(self.dtype)
        data /= 1e4
        return data



class _basicTCFcell:
    '''
    It contains only data, not attributes
    '''
    @multimethod
    def __init__(self, properties:dict):
        self.properties = properties

    @multimethod
    def __init__(self, f:h5py._hl.group.Group):
        self.properties = dict()
        for key in f.keys():
            self[key] = f[key][()]
    
    def __getitem__(self, key:str):
        return self.properties[key]
    
    def __setitem__(self, key:str, item):
        self.properties[key] = item
    
    def __delitem__(self, key:str):
        del self.properties[key]
    
    def keys(self):
        return self.properties.keys()
    
    def items(self):
        return self.properties.items()

    def save(self, io):
        for key in self.keys():
            io.create_dataset(key, data = self[key])
            
class TCFcell(_basicTCFcell):

    @multimethod
    def __init__(self, tcfile:TCFile, idx:int, properties = None, **kwargs):
        if properties is None:
            properties = kwargs
        elif len(kwargs) > 0:
            properties.update(kwargs)
        super().__init__(properties)
        # attributes
        self.tcfname = tcfile.tcfname
        self.resol = tcfile.resol
        self.imgtype = tcfile.imgtype
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
                self.imgtype = _ImgDim(f.attrs['imgtype'])
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
            f.attrs['imgtype'] = self.imgtype.value

class TCFcell_t:

    @multimethod
    def __init__(self, tcfcells:List[TCFcell]):
        '''
        validation
        - each tcfcells comes from the same tcfile with incrementing index (TODO)
        '''
        

        self.tcfcells = [_basicTCFcell(tcfcell.properties) if tcfcell is not None else None for tcfcell in tcfcells]
        self.tcfname = tcfcells[0].tcfname
        self.imgtype = tcfcells[0].imgtype
        self.len = len(TCFile(self.tcfname, self.imgtype.value))

    @multimethod
    def __init__(self, fname:str):
        with h5py.File(fname,'r') as f:
            if f.attrs["type"] == 'TCFcell_t':
                self.tcfname = f.attrs['tcfname']
                length = f.attrs['len']
                self.tcfcells = [None] * length
                for id in f.keys():
                    i = int(id)
                    self.tcfcells[i] = _basicTCFcell(f[id])
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