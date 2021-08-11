#pip install -e C:\Users\labdo\Desktop\Tomocell
from Tomocell import *
from time import time
x = TCFile('D:/Neutrophil-Centrifugation/20210729.165038.193.LMJ-Neutrophil-006/20210729.165038.193.LMJ-Neutrophil-006.TCF','3D')

# test1
for i in x:
    print(x.shape)

# test2
data = x[0]
cellmask, cellcnt = Cellmask(data)
cellproperties(data, cellmask, cellcnt, 1.337, x.Volpix,minvol=200)

#test3
fig, ax = plt.subplots(); Slice3dviewer(data, ax); plt.show()

#test4
tic=time(); tcfcells_t = [get_celldata(x, i, mindm=30) for i in range(len(x))]; toc =time();print(toc-tic)

#test5
connect_tcfcells_t = get_celldata_t(tcfcells_t)