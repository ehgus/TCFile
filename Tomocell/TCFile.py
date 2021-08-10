import h5py
import numpy as np
from typing import List, Union
from multimethod import multimethod

class TCFile:
    def __init__(self, TCFname:str, dtype:str) -> None:
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

    def __init__(self, CM:tuple,resol:tuple, volume:float, drymass:float, tcfname:str, idx:int) -> None:
        self.CM = CM
        self.volume = volume
        self.drymass = drymass
        self.resol = resol
        # attributes
        self.tcfname = tcfname
        self.idx = idx
    
    def __init__(self, fname:str) -> None:
        with h5py.File(fname,'r') as f:
            if f.attrs['type'] == 'TCFcell':
                self.tcfname = f.attrs['tcfname']
                self.idx = f.attrs['idx']
                self.CM = f['CM'][:]
                self.volume = f['volume'][:]
                self.drymass = f['drymass'][:]
                self.resol = f['resol'][:]
            else:
                NameError('The file does not support TCFcell')

    def __init__(self, f:h5py._hl.files.File, tcfname, idx) -> None:
        self.CM = f['CM'][:]
        self.volume = f['volume'][:]
        self.drymass = f['drymass'][:]
        self.resol = f['resol'][:]
        # attributes
        self.tcfname = tcfname
        self.idx = idx
        pass

    def __repr__(self) -> str:
        data_repr = (f'Center of Mass: {repr(self.CM)} pixel\n'
                     f'Volume: {repr(self.volume)} μm³\n'
                     f'dry mass: {repr(self.drymass)} pg')
        return data_repr
    
    def save(self, fname:str):
        with h5py.File(fname,'w') as f:
            f.attrs['type'] = 'TCFcell'
            f.attrs['tcfname'] = self.tcfname
            f.attrs['idx'] = self.idx
            f.create_dataset('Volume', data = self.volume)
            f.create_dataset('Mass', data = self.drymass)
            f.create_dataset('CM', data = self.CM)
            f.create_dataset('resol', data = self.resol)

class TCFcell_t:

    @multimethod
    def __init__(self, tcfcells:List[TCFcell]) -> None:
        '''
        validation
        - each tcfcells comes from the same tcfile with incrementing index (TODO)
        '''
        self.tcfcells = tcfcells
        self.len = len(tcfcells)
        self.tcfname = tcfcells[0].tcfname

    @multimethod
    def __init__(self, fname:str) -> None:
        with h5py.File(fname,'r') as f:
            if f.attrs["type"] == 'TCFcell_t':
                self.tcfname = f.attrs['tcfname']
                self.len = f.attrs['len']
                self.tcfcells = [TCFcell(f[f'{i:06d}'],self.tcfname,i) for i in range(self.len)]
            else:
                NameError('The file does not support TCFcell_t')
    
    def __getitem__(self, key:int) -> TCFcell:
        return self.tcfcells[key]
    
    def __setitem__(self, key:int, item:TCFcell) -> None:
        self.tcfcells[key] = item
    
    def __len__(self) -> int:
        return self.len

    def save(self, fname:str):
        with h5py.File(fname,'w') as f:
            f.attrs['type'] = 'TCFcell_t'
            f.attrs['tcfname'] = self.tcfname
            f.attrs['len'] = self.len
            for i in range(self.len):
                id = f'{i:06d}'
                f.create_dataset(f'{id}/Volume', data = self.tcfcells[i].volume)
                f.create_dataset(f'{id}/Mass', data = self.tcfcells[i].drymass)
                f.create_dataset(f'{id}/CM', data = self.tcfcells[i].CM)
                f.create_dataset(f'{id}/resol', data = self.tcfcells[i].resol)