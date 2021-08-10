from scipy.spatial import distance
from skimage import filters
from scipy.ndimage import binary_dilation, binary_erosion, binary_fill_holes, label, labeled_comprehension, center_of_mass
from scipy.spatial.distance import cdist
import numpy as np
import warnings
from . import *


def _default_cellmask(img:np.ndarray):
    
    def diamond_kernel(r, dim):
        def kernelfunc(*args):
            return sum([np.abs(idx-r) for idx in args]) <= r
        return np.fromfunction(kernelfunc, tuple(2*r+1 for _ in range(dim)), dtype = int)

    kernel = diamond_kernel(2,len(img.shape))
    kernel2 = diamond_kernel(4,len(img.shape))

    otsu_val = filters.threshold_otsu(img)
    _b_cellmask = img > otsu_val
    _b2_cellmask = np.empty(_b_cellmask, dtype = _b_cellmask.dtype)
    # bottleneck!
    binary_erosion(_b_cellmask, structure=kernel, output = _b2_cellmask)
    binary_dilation(_b2_cellmask, structure=kernel2, output = _b_cellmask)
    binary_fill_holes(_b_cellmask, output = _b2_cellmask)
    binary_erosion(_b2_cellmask, structure=kernel, output = _b_cellmask)

    cellmask, lbl = label(_b_cellmask)
    return cellmask, lbl

def get_celldata(tcfile:TCFile, index:int, bgRI = 1.337, cellmask_func = _default_cellmask, **constrants):
    '''
    img should contain RI information
    '''
    # get basic data
    img = tcfile[index]
    Volpix = tcfile.Volpix
    tcfname = tcfile.TCFname

    # generate labeled mask
    cellmask, lbl = cellmask_func(img)
    lbls = range(1,lbl+1)

    # evaluate physical parameters
    Volume = np.array([np.count_nonzero(cellmask == lbl)*Volpix for lbl in lbls]) # (μm)^D (D:dimensions)
    if 'minvol' in constrants.keys():
        limit = Volume > constrants['minvol']
        Volume = Volume[limit]
        lbls = lbls[limit]
    if 'maxvol' in constrants.keys():
        limit = Volume < constrants['maxvol']
        Volume = Volume[limit]
        lbls = lbls[limit]

    Drymass = labeled_comprehension(img - bgRI, cellmask, lbls, lambda x: np.sum(x)/0.185,float, None) # pg
    if 'mindm' in constrants.keys():
        limit = Drymass > constrants['mindm']
        Drymass = Drymass[limit]
        lbls = lbls[limit]
    if 'maxm' in constrants.keys():
        limit = Drymass < constrants['maxm']
        Drymass = Drymass[limit]
        lbls = lbls[limit]

    CenterOfMass = center_of_mass(img, cellmask, lbls)

    return [TCFcell(cm, vol, dm, tcfname, index) for cm,vol, dm in zip(CenterOfMass, Volume, Drymass)]

def _default_connectivity(bf_tcfcells,af_tcfcells):
    '''
    input: list of TCFcells

    '''
    # do you know kimchi?
    # do you know psy?
    # do you know gangnam style?
    # do you know Dokdo?
    distance = cdist(bf_tcfcells, af_tcfcells)
    connectivity = [np.argmin(distance[i,:]) for i in range(len(bf_tcfcells))]
    return connectivity

def get_celldata_t(tcfcells_tlapse:List[List[TCFcell]], connectivity_func = _default_connectivity):
    '''
    tcfcells_tlapse: list of (each time point) list of (each cells) TCFcells 
    return multiple TCFcell_t
    check and warn: if # of TCFcells for each time section does not match, it generate warning 
    TODO: soft tracking when it fails 

    try to do:
    Hysteresis thresholding
    watershed algorithm
    '''
    tcfcell_ts = [TCFcell_t([tcfcell]) for tcfcell in range(tcfcells_tlapse[0])]
    tcfcell_index_bf = list(range(len(tcfcells_tlapse[0])))
    for i in range(len(tcfcells_tlapse)-1):
        bf_tcfcells = tcfcells_tlapse[i]
        af_tcfcells = tcfcells_tlapse[i+1]
        if len(bf_tcfcells) != len(af_tcfcells):
            warnings.warn('number of cells are mismatched') # Is it the best?
        connectivity = connectivity_func(bf_tcfcells,af_tcfcells)
        tcfcell_idx = tcfcell_index_bf[i]
        # to be continued
    pass