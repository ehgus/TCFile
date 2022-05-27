import numpy as np
import cv2 as cv
import scipy.ndimage as ndi
from .. import *

def get_morphology(tcfcell:TCFcell):
    # get cellmask slice
    cellmask = tcfcell['mask']
    def _itr_or(array):
        # boolean array
        z = array.shape[0]
        if z == 1:
            return np.squeeze(array,0)
        if z == 2:
            return np.logical_or(array[0,:,:],array[1,:,:],out=array[0,:,:])
        else:
            zhalf = z//2
            return np.logical_or(_itr_or(array[:zhalf]),_itr_or(array[zhalf:]))
    cellmask_slice = ndi.binary_fill_holes(_itr_or(cellmask)).astype(np.uint8)
    cellmask_slice[cellmask_slice > 0] = 255
    # find morphologies
    countour, hierarchy = cv.findContours(cellmask_slice,cv.RETR_LIST, cv.CHAIN_APPROX_NONE)
    cnt = countour[0]
    
    center_rect,size_rect,angle_rect = cv.minAreaRect(cnt) # angle is in degree
    tcfcell['centerR'] = center_rect
    tcfcell['sizeR'] = size_rect
    tcfcell['angleR'] = angle_rect
    if len(cnt) > 5:
        ellipse = cv.fitEllipse(cnt)
        tcfcell['centerE'] = ellipse[0]
        tcfcell['rotE'] = ellipse[2]
        tcfcell['widthE'] = ellipse[1][0]
        tcfcell['heightE'] = ellipse[1][1]

def get_ellipsoid(tcfcell:TCFcell):
    cellmask = tcfcell['mask'].astype(np.uint8)
    cellmask[cellmask > 0] = 255

    # find contours
    points = []
    for z in range(cellmask.shape[0]):
        cellmask_slice = cellmask[z,...]
        contour, hierarchy = cv.findContours(cellmask_slice,cv.RETR_LIST, cv.CHAIN_APPROX_NONE)
        if len(contour) == 0:
            continue
        else:
            points_slice = np.empty((contour[0].shape[0],3),dtype=np.uint16)
            points_slice[:,0] = z
            points_slice[:,1] = contour[0][:,0,1] #y
            points_slice[:,2] = contour[0][:,0,0] #x
            points.append(points_slice)
    points = np.concatenate(points)
    center, evecs, radii = ellipsoid_fit(points)
    tcfcell['center_Ellipsoid'] = tuple(center)
    tcfcell['evecs_Ellipsoid'] = tuple(evecs)
    tcfcell['radii_Ellipsoid'] = tuple(radii)


# https://github.com/aleksandrbazhin/ellipsoid_fit_python
def ellipsoid_fit(X):
    x = X[:, 0]
    y = X[:, 1]
    z = X[:, 2]
    D = np.array([x * x + y * y - 2 * z * z,
                 x * x + z * z - 2 * y * y,
                 2 * x * y,
                 2 * x * z,
                 2 * y * z,
                 2 * x,
                 2 * y,
                 2 * z,
                 1 - 0 * x])
    d2 = np.array(x * x + y * y + z * z).T # rhs for LLSQ
    u = np.linalg.solve(D.dot(D.T), D.dot(d2))
    a = np.array([u[0] + 1 * u[1] - 1])
    b = np.array([u[0] - 2 * u[1] - 1])
    c = np.array([u[1] - 2 * u[0] - 1])
    v = np.concatenate([a, b, c, u[2:]], axis=0).flatten()
    A = np.array([[v[0], v[3], v[4], v[6]],
                  [v[3], v[1], v[5], v[7]],
                  [v[4], v[5], v[2], v[8]],
                  [v[6], v[7], v[8], v[9]]])

    center = np.linalg.solve(- A[:3, :3], v[6:9])

    translation_matrix = np.eye(4)
    translation_matrix[3, :3] = center.T

    R = translation_matrix.dot(A).dot(translation_matrix.T)

    evals, evecs = np.linalg.eig(R[:3, :3] / -R[3, 3])
    evecs = evecs.T

    radii = np.sqrt(1. / np.abs(evals))
    radii *= np.sign(evals)

    return center, evecs, radii
