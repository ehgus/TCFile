from skimage import filters
import scipy.ndimage as ndi
from scipy.spatial.distance import cdist
import numpy as np
from . import *

def __diamond_kernel(r, dim):
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

def get_celldata(tcfile:TCFile, index:int, bgRI = 1.337, cellmask_func = _default_cellmask, **constrants):
    '''
    img should contain RI information
    '''
    # get basic data
    data = tcfile[index]
    Volpix = tcfile.Volpix
    tcfname = tcfile.TCFname
    resol = tcfile.resol
    # generate labeled mask
    cellmask, lbl = cellmask_func(data)
    lbls = np.arange(1,lbl+1)

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

    Drymass = ndi.labeled_comprehension(data/1e4 - bgRI, cellmask, lbls, lambda x: np.sum(x)*(Volpix/0.185),float, None) # pg
    if 'mindm' in constrants.keys():
        limit = Drymass > constrants['mindm']
        Drymass = Drymass[limit]
        lbls = lbls[limit]
    if 'maxdm' in constrants.keys():
        limit = Drymass < constrants['maxdm']
        Drymass = Drymass[limit]
        lbls = lbls[limit]

    CenterOfMass = ndi.center_of_mass(data, cellmask, lbls)

    return [TCFcell(cm, resol, vol, dm, tcfname, index) for cm,vol, dm in zip(CenterOfMass, Volume, Drymass)]

def _default_connectivity(bf_tcfcells:List[TCFcell], af_tcfcells:List[TCFcell]) -> List[Union[TCFcell, None]]:
    '''
    input: list of TCFcells
    Assumption: space b/w the Ceter of cells is large enough compared
    to its movement given time interval.
    '''
    bf_cm = np.array([x.CM for x in bf_tcfcells])
    af_cm = np.array([x.CM for x in af_tcfcells])
    distance = cdist(bf_cm, af_cm)
    connectivity = list(np.argmin(distance, axis=0)) # af(key) -> bf(val)
    return connectivity

def get_celldata_t(tcfcells_tlapse:List[List[TCFcell]], connectivity_func = _default_connectivity):
    '''
    tcfcells_tlapse: list of (each time point) list of (each cells) TCFcells
    return multiple TCFcell_t
    check and warn: if # of TCFcells for each time section does not match, it generate warning 
    TODO: soft tracking when it fails 

    if They are ill distributed, then it will just find partial t cells
    '''
    tcfcell_t_stack = [TCFcell_t([tcfcell]) for tcfcell in tcfcells_tlapse[0]]
    connectivity = list(range(len(tcfcell_t_stack))) # direct current point -> initial point
    for i in range(len(tcfcells_tlapse)-1):
        bf_tcfcells = tcfcells_tlapse[i]
        af_tcfcells = tcfcells_tlapse[i+1]
        if len(bf_tcfcells) != len(af_tcfcells):
            raise ValueError('number of cells are mismatched')
        connectivity = [connectivity[bf] for bf in connectivity_func(bf_tcfcells,af_tcfcells)]
        for (cell_idx, cell_t_idx) in enumerate(connectivity):
            tcfcell_t_stack[cell_t_idx].append(af_tcfcells[cell_idx])
    return tcfcell_t_stack