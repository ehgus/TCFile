from typing import Union, List
from ..TCFhandler import *
import numpy as np
from scipy.spatial.distance import cdist

def _default_connectivity(bf_tcfcells:List[TCFcell], af_tcfcells:List[TCFcell]) -> List[Union[TCFcell, None]]:
    '''
    input: list of TCFcells
    Assumption: space b/w the Ceter of cells is large enough compared
    to its movement given time interval.
    '''
    bf_cm = np.array([x.CMass for x in bf_tcfcells])
    af_cm = np.array([x.CMass for x in af_tcfcells])
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