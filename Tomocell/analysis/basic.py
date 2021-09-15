import enum
from numpy.core.fromnumeric import argmin
from skimage import filters
import scipy.ndimage as ndi
from scipy.spatial.distance import cdist
import numpy as np
from warnings import warn
from typing import Union, List
from .. import *

def __diamond_kernel(r, dim) -> np.ndarray:
    kernelfunc = lambda *args: sum([np.abs(idx-r) for idx in args]) <= r
    return np.fromfunction(kernelfunc, tuple(2*r+1 for _ in range(dim)), dtype = int)

def _default_cellmask(img:np.ndarray):
    kernel = __diamond_kernel(1,len(img.shape))
    otsu_val = filters.threshold_otsu(img)
    _b_cellmask = img > otsu_val
    _b2_cellmask = np.empty_like(_b_cellmask, dtype = _b_cellmask.dtype)
    # bottleneck!
    # see this issues before you modify the next codes: https://github.com/scipy/scipy/issues/13991#issuecomment-839853868
    ndi.binary_erosion(_b_cellmask, structure=kernel, iterations = 2, output = _b2_cellmask)
    ndi.binary_dilation(_b2_cellmask, structure=kernel, iterations = 4, output = _b_cellmask)
    ndi.binary_fill_holes(_b_cellmask, output = _b2_cellmask)
    ndi.binary_erosion(_b2_cellmask, structure=kernel, iterations = 2, output = _b_cellmask)

    cellmask, lbl = ndi.label(_b_cellmask)
    return cellmask, lbl

def get_celldata(tcfile:TCFile, index:int, bgRI = 1.337, cellmask_func = _default_cellmask,rtn_cellmask = False, **constraints) -> List[TCFcell]:
    '''
    img should contain RI information
    '''
    # get basic data
    data = tcfile[index] - bgRI
    Volpix = tcfile.Volpix
    # generate labeled mask
    cellmask, lbl = cellmask_func(data)
    lbls = np.arange(1,lbl+1)

    # evaluate physical parameters
    Volume = np.fromiter((np.count_nonzero(cellmask == lbl)*Volpix for lbl in lbls),float) # (μm)^D (D:dimensions)
    if 'minvol' in constraints.keys():
        limit = Volume > constraints['minvol']
        Volume = Volume[limit]
        lbls = lbls[limit]
    if 'maxvol' in constraints.keys():
        limit = Volume < constraints['maxvol']
        Volume = Volume[limit]
        lbls = lbls[limit]

    Drymass = ndi.labeled_comprehension(data, cellmask, lbls, lambda x: np.sum(x)*Volpix/0.185,float, None) # pg
    if 'mindm' in constraints.keys():
        limit = Drymass > constraints['mindm']
        Drymass = Drymass[limit]
        lbls = lbls[limit]
    if 'maxdm' in constraints.keys():
        limit = Drymass < constraints['maxdm']
        Drymass = Drymass[limit]
        lbls = lbls[limit]
    
    def _center_of_mass(data):
        indices = (np.arange(1,data.ndim+1).reshape(-1,1) + np.arange(data.ndim-1).reshape(1,-1))%data.ndim
        partial_sum = [np.sum(data,tuple(idx)) for idx in indices]
        norm = np.sum(partial_sum[0])
        grids = [np.arange(size) for size in data.shape]
        result = [np.sum(idx_sum*grid)/norm for idx_sum,grid in zip(partial_sum, grids)]
        return tuple(result)
    CenterOfMass = [_center_of_mass(data*(cellmask==lbl)) for lbl in lbls]

    tcfcells = [TCFcell(tcfile, index, CM=CM, volume=volume, drymass=drymass) for CM, volume, drymass in zip(CenterOfMass, Volume, Drymass)]
    if rtn_cellmask:
        for tcfcell,idx in zip(tcfcells, lbls):
            tcfcellmask = (cellmask== idx)
            tcfcell['mask'] = tcfcellmask

    return tcfcells

def _default_connectivity(bf_tcfcells:List[TCFcell], af_tcfcells:List[TCFcell]) -> List[Union[int, None]]:
    '''
    input: list of TCFcells
    Assumption: space b/w the Ceter of cells is large enough compared
    to its movement given time interval.
    '''
    if len(bf_tcfcells) == 0 or len(af_tcfcells) == 0:
        return [None] * len(af_tcfcells)
    bf_cm = np.array([x['CM'] for x in bf_tcfcells])
    af_cm = np.array([x['CM'] for x in af_tcfcells])
    distance = cdist(bf_cm, af_cm)
    if len(af_cm) <= len(bf_cm):
        connectivity = list(np.argmin(distance, axis=0))
    else:
        _connectivity = list(np.argmin(distance, axis=1))
        connectivity = [_connectivity.index(i) if i in _connectivity else None for i in range(len(af_cm))]

    return connectivity # af_tcfcells[idx] <-> bf_tcfcells[val]

def get_celldata_t(tcfcells_tlapse:List[List[TCFcell]], connectivity_func = _default_connectivity) -> List[TCFcell_t]:
    '''
    tcfcells_tlapse: list of (each time point) list of (each cells) TCFcells
    return multiple TCFcell_t
    check and warn: if # of TCFcells for each time section does not match, it generate warning 
    TODO: soft tracking when it fails 

    if They are ill distributed, then it will just find partial t cells
    '''
    tcfcell_t_final = []
    tcfcell_t_stack = [TCFcell_t([tcfcell]) for tcfcell in tcfcells_tlapse[0]]
    connectivity = list(range(len(tcfcell_t_stack))) # direct current point -> initial point
    for i in range(1, len(tcfcells_tlapse)):
        bf_tcfcells = tcfcells_tlapse[i-1]
        af_tcfcells = tcfcells_tlapse[i]
        # concat
        connectivity = connectivity_func(bf_tcfcells, af_tcfcells)
        for bf_tcfcell_loc, af_tcfcell in zip(connectivity, af_tcfcells):
            if bf_tcfcell_loc != None:
                tcfcell_t_stack[bf_tcfcell_loc].append(af_tcfcell)
        # flush part of tcfcell_t
        for i, tcfcell_t in enumerate(tcfcell_t_stack):
            if i not in connectivity:
                tcfcell_t_final.append(tcfcell_t)
        # relocation
        tcfcell_t_stack = [TCFcell_t([af_tcfcells[af_tcfcell_loc]]) if bf_tcfcell_loc is None else tcfcell_t_stack[bf_tcfcell_loc] for af_tcfcell_loc,bf_tcfcell_loc in enumerate(connectivity)]

    tcfcell_t_final.extend(tcfcell_t_stack)
    return tcfcell_t_final