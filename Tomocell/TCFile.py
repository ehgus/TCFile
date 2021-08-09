import h5py
import os
import numpy as np

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
    
    def __getitem__ (self, item:int) -> np.ndarray:
        '''
        '''
        if item >= self.len:
            raise IndexError(f'{TCFile.__name__} index out of range')
        with h5py.File(self.TCFname) as f:
            data = f[f'Data/{self.dtype}/{item:06d}'][:]
        return data

    def __len__(self) -> int:
        return self.len
        
