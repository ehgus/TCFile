from Tomocell import *
x = TCFile('D:/Neutrophil-Centrifugation/20210729.165038.193.LMJ-Neutrophil-006/20210729.165038.193.LMJ-Neutrophil-006.TCF','3D')

# test1
for i in x:
    print(x.shape)

# test2
data = x[0]
cellmask, cellcnt = Cellmask(data)
cellprofiling(data, cellmask, cellcnt, 1.337, x.Volpix)

#test3
fig, ax = plt.subplots()
Slice3dviewer(data, ax)