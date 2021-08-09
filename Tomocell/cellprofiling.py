from skimage import filters
from scipy.ndimage import binary_dilation, binary_erosion, binary_fill_holes, label, labeled_comprehension, center_of_mass
import numpy as np

def diamond_kernel(r, dim):
    def kernelfunc(*args):
        return sum([np.abs(idx-r) for idx in args]) <= r
    return np.fromfunction(kernelfunc, tuple(2*r+1 for _ in range(dim)), dtype = int)


def Cellmask(img:np.ndarray):
    kernel = diamond_kernel(2,len(img.shape))

    otsu_val = filters.threshold_otsu(img)
    _b_cellmask = img > otsu_val
    binary_erosion(_b_cellmask, structure=kernel, output = _b_cellmask)

    binary_dilation(_b_cellmask, structure=kernel,iterations=2, output = _b_cellmask)
    binary_fill_holes(_b_cellmask, output = _b_cellmask)
    binary_erosion(_b_cellmask, structure=kernel, output = _b_cellmask)

    return label(_b_cellmask)

def cellprofiling(img, cellmask, cellcnt, bgRI, Volpix):
    '''
    img should contain RI information
    '''
    lbls = np.arange(1,cellcnt+1)
    return [
        center_of_mass(img, cellmask, lbls),
        labeled_comprehension(img - bgRI, cellmask, lbls, lambda x: np.sum(x)/0.185,float, None), # dry mass
        [np.count_nonzero(cellmask == lbl)*Volpix for lbl in lbls],
    ]