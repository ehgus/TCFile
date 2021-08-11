import numpy as np
from numpy.core.numeric import zeros_like
from scipy.ndimage.measurements import center_of_mass
import cv2 as cv
from . import *

def get_morphology(tcfcell:TCFcell):
    # find optimal z axis
    cellmask = tcfcell['mask']

    opt_z = 0
    maxz = 0
    for z,cellmask_slice in enumerate(cellmask):
        cnt = np.count_nonzero(cellmask_slice)
        if cnt > maxz:
            maxz = cnt
            opt_z = z
    # find morphologies
    cellmask_slice = cellmask[opt_z,...].astype(np.uint8)
    cellmask_slice[cellmask_slice > 0] = 255
    countour, hierarchy = cv.findContours(cellmask_slice,cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
    cnt = countour[0]
    
    center_rect = np.array(cv.minAreaRect(cnt)[0])
    polarity = (tcfcell['CM'][:2] - center_rect)*tcfcell['resol'][:2] # unit: μm
    tcfcell['polarity'] = polarity
    if len(cnt) > 5:
        ellipse = cv.fitEllipse(cnt)
        tcfcell['centerE'] = ellipse[0]
        tcfcell['rotE'] = ellipse[2]
        tcfcell['widthE'] = ellipse[1][0]
        tcfcell['heightE'] = ellipse[1][1]

