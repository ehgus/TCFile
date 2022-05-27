from curses import has_key
from typing import List

from numpy import isin
from . import TCFile
import h5py
from multimethod import multimethod

class TCFcell:
    '''
    It contains physical information of specific cell.
    It may contains cell mask, or center of mass only.


    Attributes
    ----------
    DMass : float
        Dry mass of the cell. The unit is `pg`
    Vol : ndarray
        Volume of the cell. The unit is `μm^D` where D is its imgtypeension (2 or 3).
    CMass : ndarray
        center of mass. it is expressed as
    mask : ndarray
        mask of cell
    properties : doct
        place to store custom properties
    '''
    @multimethod
    def __init__(self, tcfile, imgidx, DMass, Vol, CMass, mask = None):
        # file attributes
        if isinstance(tcfile,str):
            self.tcfname = tcfile
        elif isinstance(tcfile,TCFile):
            self.tcfname = tcfile.tcfname
        else:
            assert()
        self.imgtype = tcfile.imgtype
        self.imgidx = imgidx
        # cell properties
        self.DMass = DMass
        self.Vol = Vol
        self.CMass = CMass
        self.mask = mask
    
    @multimethod
    def __init__(self, fname:str):
        with h5py.File(fname, 'r') as f:
            if  'type' not in f.attrs.keys() or f.attrs['type'] != 'TCFcell':
                NameError('The file does not support TCFcell')

            # file attributes
            self.tcfname = f.attrs['tcfname']
            self.imgtype = f.attrs['imgtype']
            self.index = f.attrs['index']
            # cell value
            self.properties = dict()
            for key in f.keys():
                if key in ('DMass', 'Vol', 'CMass'):
                    setattr(self, key, f.attrs[key])
                else:
                    self.properties[key] = f.attrs[key]

    def save(self, fname:str):
        with h5py.File(fname,'w') as f:
            # checksum
            f.attrs['type'] = 'TCFcell'
            # file attributes
            f.attrs['tcfname'] = self.tcfname
            f.attrs['imgtype'] = self.imgtype
            f.attrs['index'] = self.index
            # cell value
            for key in ('CMass','DMass', 'Vol','mask'):
                if hasattr(f, key):
                    f.attrs[key] = getattr(self, key)

    def __getitem__(self, key:str):
        if key in ('DMass', 'Vol', 'CMass'):
            value = getattr(self, key) 
        else:
            value = self.properties[key]
        return value

    def __setitem__(self, key:str, value):
        if key in ('DMass', 'Vol', 'CMass'):
            setattr(self, key, value)
        else:
            self.properties[key] = value

class TCFcell_t:

    @multimethod
    def __init__(self, tcfcells:List[TCFcell]):
        '''
        validation

        TODO
        - store/load custom properties
        - 
        '''
        # file attributes
        self.tcfname = tcfcells[0].tcfname
        self.imgtype = tcfcells[0].imgtype
        self.len = len(TCFile(self.tcfname, self.imgtype))
        for tcfcell in tcfcells:
            assert tcfcell.tcfname == self.tcfname, 'All tcfcell should come from the same TCF file'
            assert tcfcell.imgtype == self.imgtype, 'All tcfcell sould be calculated in the same tyeps of data'
        # cell values
        for attr in ('DMass', 'Vol', 'CMass'):
                setattr(self, attr, [None] * self.len)
        for tcfcell in tcfcells:
            index = tcfcell.index
            for attr in ('DMass', 'Vol', 'CMass'):
                datalist = getattr(self, attr)
                datalist[index] = getattr(tcfcell, attr)

    @multimethod
    def __init__(self, fname:str):
        with h5py.File(fname,'r') as f:
            if 'type' not in f.attrs.keys() or f.attrs["type"] != 'TCFcell_t':
                NameError('The file does not support TCFcell_t')

            # file attributes
            self.tcfname = f.attrs['tcfname']
            self.imgtype = f.attrs['imgtype']
            self.len = len(TCFile(self.tcfname, self.imgtype))
            # cell value
            for attr in ('DMass', 'Vol', 'CMass'):
                setattr(self, attr, [None] * self.len)
            for key in f.keys():
                grp = f[key]
                index = int(key)
                for attr in ('DMass', 'Vol', 'CMass'):
                    datalist = getattr(self, attr)
                    try:
                        datalist[index] = grp.attrs[attr]
                    except:
                        pass

    def save(self, fname:str):
        with h5py.File(fname,'w') as f:
            # checksum
            f.attrs['type'] = 'TCFcell_t'
            # file attributes
            f.attrs['tcfname'] = self.tcfname
            f.attrs['imgtype'] = self.imgtype
            # cell value
            for index, value in enumerate(self.Vol):
                if value is None:
                    continue
                grp = f.create_group(f'{index:06d}')
                for attr in ('DMass', 'Vol', 'CMass'):
                    datalist = getattr(self, attr)
                    if datalist is None:
                        continue
                    grp.attrs[attr] = datalist[index]

    def __len__(self) -> int:
        return self.len

    def append(self, tcfcell:TCFcell):
        assert tcfcell.tcfname == self.tcfname, 'All tcfcell should come from the same TCF file'
        assert tcfcell.imgtype == self.imgtype, 'All tcfcell sould be calculated in the same tyeps of data'
        # cell values
        index = tcfcell.index
        for attr in ('DMass', 'Vol', 'CMass'):
            datalist = getattr(self, attr)
            datalist[index] = getattr(tcfcell, attr)


