import h5py
import numpy as np
from typing import List, Union
from multimethod import multimethod

class TCFile:
    def __init__(self, TCFname:str, dtype:str):
        '''
        object that ease the TCF data manupulation

        validation checkstep
        - dtype validation
            - only support "2D" and "3D"
            - check whether if the dtype is supported in the TCFile
        '''
        if dtype not in ('2D', '3D'):
            raise ValueError('dtype only support "2D" and "3D"')

        self.TCFname=TCFname
        self.dtype=dtype
        
        with h5py.File(TCFname) as f:
            if dtype not in f['Data']:
                raise ValueError('The TCFile does not support the suggested file')
            getAttr = lambda name: f[f'Data/{dtype}'].attrs[name][0]
            self.len = getAttr('DataCount')
            self.shape = tuple(getAttr(f'Size{idx}') for idx in  ('Z', 'Y', 'X'))
            self.resol = tuple(getAttr(f'Resolution{idx}') for idx in  ('Z', 'Y', 'X'))
            self.Volpix = np.prod(self.resol) #  # (μm)^D (D:dimensions)
            self.dt = 0 if self.len == 1 else getAttr('TimeInterval') # s
    
    def __getitem__ (self, key:int) -> np.ndarray:
        '''
        '''
        if key >= self.len:
            raise IndexError(f'{TCFile.__name__} index out of range')
        with h5py.File(self.TCFname) as f:
            data = f[f'Data/{self.dtype}/{key:06d}'][:]
        return data

    def __len__(self) -> int:
        return self.len
        
class TCFcell:

    @multimethod
    def __init__(self, CM:tuple,resol:tuple, volume:float, drymass:float, tcfname:str, idx:int):
        self.CM = CM
        self.volume = volume
        self.drymass = drymass
        self.resol = resol
        # attributes
        self.tcfname = tcfname
        self.idx = idx
    
    @multimethod
    def __init__(self, f:h5py._hl.group.Group, tcfname:str, idx:int):
        self.CM = f['CM'][:]
        self.resol = f['resol'][:]
        self.volume = f['volume'][()]
        self.drymass = f['drymass'][()]
        # attributes
        self.tcfname = tcfname
        self.idx = idx

    @multimethod
    def __init__(self, fname:str):
        with h5py.File(fname,'r') as f:
            if f.attrs['type'] == 'TCFcell':
                self.tcfname = f.attrs['tcfname']
                self.idx = f.attrs['idx']
                self.CM = f['CM'][:]
                self.resol = f['resol'][:]
                self.volume = f['volume'][()]
                self.drymass = f['drymass'][()]
            else:
                NameError('The file does not support TCFcell')

    

    def __repr__(self) -> str:
        data_repr = (f'Center of Mass: ({",".join(["{0:.2f} ".format(v) for v in self.CM])}) pixel\n'
                     f'volume: {repr(self.volume)} μm³\n'
                     f'dry mass: {repr(self.drymass)} pg\n')
        return data_repr
    
    def save(self, fname:str):
        with h5py.File(fname,'w') as f:
            f.attrs['type'] = 'TCFcell'
            f.attrs['tcfname'] = self.tcfname
            f.attrs['idx'] = self.idx
            f.create_dataset('volume', data = self.volume)
            f.create_dataset('drymass', data = self.drymass)
            f.create_dataset('CM', data = self.CM)
            f.create_dataset('resol', data = self.resol)

class TCFcell_t:

    @multimethod
    def __init__(self, tcfcells:List[Union[TCFcell,None]]):
        '''
        validation
        - each tcfcells comes from the same tcfile with incrementing index (TODO)
        '''
        self.tcfcells = tcfcells
        self.tcfname = tcfcells[0].tcfname

    @multimethod
    def __init__(self, fname:str):
        with h5py.File(fname,'r') as f:
            if f.attrs["type"] == 'TCFcell_t':
                self.tcfname = f.attrs['tcfname']
                length = f.attrs['len']
                self.tcfcells = [None] * length
                for id in f.keys():
                    i = int(id)
                    self.tcfcells[i] = TCFcell(f[id],self.tcfname, i)
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
            for i in range(len(self)):
                if self.tcfcells[i] is None:
                    continue
                id = f'{i:06d}'
                f.create_dataset(f'{id}/volume', data = self.tcfcells[i].volume)
                f.create_dataset(f'{id}/drymass', data = self.tcfcells[i].drymass)
                f.create_dataset(f'{id}/CM', data = self.tcfcells[i].CM)
                f.create_dataset(f'{id}/resol', data = self.tcfcells[i].resol)