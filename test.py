#pip install -e C:\Users\labdo\Desktop\Tomocell
from Tomocell import *
from time import time
x = TCFile('D:/Neutrophil-Centrifugation/20210729.165038.193.LMJ-Neutrophil-006/20210729.165038.193.LMJ-Neutrophil-006.TCF','3D')
data = x[0]
# test1
for i in x:
    print(x.shape)

# test2
cellmask, cellcnt = Cellmask(data)
cellproperties(data, cellmask, cellcnt, 1.337, x.Volpix,minvol=200)

#test3
fig, ax = plt.subplots();slicer = slice3dviewer(data, ax); fig.show()
slicer.add_point((100,100),z=40)
slicer.add_arrow((100,100),(150,150),width=10)

#test4: 73s -> 45s
tic=time(); tcfcells_t = [get_celldata(x, i, mindm=30) for i in range(len(x))]; toc =time();print(toc-tic)

#test5
connect_tcfcells_t = get_celldata_t(tcfcells_t)