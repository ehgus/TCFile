import numpy as np
import scipy.ndimage as ndi
from skimage import filters

def _default_cellmask(img:np.ndarray):
    kernel = _diamond_kernel(1,len(img.shape))
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

def _diamond_kernel(r, dim) -> np.ndarray:
    kernelfunc = lambda *args: sum([np.abs(idx-r) for idx in args]) <= r
    return np.fromfunction(kernelfunc, tuple(2*r+1 for _ in range(dim)), dtype = int)

def compress_mask(mask:np.ndarray):
    '''
    compress mask (2D or 3D, bit array) into compressed mask + start point
    For example, assume there is a mask in the following pattern
    0   0   0   0   0
    0   1   1   1   0
    0   0   1   1   0
    0   0   0   0   0
    Then it is compressed as follows
    1   1   1
    0   1   1  , (1, 1) <- index
    '''
    assert mask.dtype == np.bool_ ,'mask should be boolean array'
    start_index = []
    stop_index = []
    indices = (np.arange(1,mask.ndim+1).reshape(-1,1) + np.arange(mask.ndim-1).reshape(1,-1))%mask.ndim
    # find all rows containing `True` mask and get start and end of the rows
    for index in indices:
        indices = list(mask.any(tuple(index)))
        start_index.append(indices.index(True))
        indices.reverse()
        stop_index.append(len(indices) - indices.index(True))
    # make compressed mask
    compressed= mask[tuple(slice(start,stop) for start, stop in zip(start_index, stop_index))]

    return compressed, start_index