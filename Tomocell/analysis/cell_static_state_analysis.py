import numpy as np
from ..TCFhandler import *
from .img_mask import _default_cellmask, compress_mask
from typing import List

def _get_center_of_mass(data):
    indices = (np.arange(1,data.ndim+1).reshape(-1,1) + np.arange(data.ndim-1).reshape(1,-1))%data.ndim
    partial_sum = [np.sum(data,tuple(idx)) for idx in indices]
    norm = np.sum(partial_sum[0])
    grids = [np.arange(size) for size in data.shape]
    result = [np.sum(idx_sum*grid)/norm for idx_sum,grid in zip(partial_sum, grids)]
    return tuple(result)

def get_celldata(tcfile:TCFile, index:int, bgRI = 1.337, rtn_cellmask = False, constraints = None) -> List[TCFcell]:
    '''
    img should contain RI information
    '''
    # get basic data
    data = tcfile[index] - bgRI
    Volpix = np.prod(tcfile.dataResolution)
    # generate labeled mask
    cellmask, labelcount = _default_cellmask(data)
    labels = np.arange(1,labelcount+1)
    # evaluate physical parameters
    tcfcells = []
    for label in labels:
        # get single cell mask
        single_mask = cellmask == label
        mask_compressed, start_index = compress_mask(single_mask)
        single_cell = mask_compressed * data[tuple(slice(start, start+length) for length, start in zip(mask_compressed.shape, start_index))]
        DMass = np.sum(single_cell)*Volpix/0.185        # pg
        Vol = np.count_nonzero(single_mask)*Volpix      # (μm)^D (D:dimensions)
        CMass = _get_center_of_mass(single_cell) + np.array(start_index)        # pixel location
        tcfcell = TCFcell(tcfile, index, DMass, Vol, CMass)
        if constraints(tcfcell):
            if rtn_cellmask:
                tcfcell['mask'] = single_mask
            tcfcells.append(tcfcell)
    return tcfcells

