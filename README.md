## Tomocell python package

Basic image processing tools of tomocube data.

## Installation

After downloading the repository, execute the following command in the repository;

```bash
pip install .
```

## Use case

```python

from Tomocell import *

tcfile = TCFile('test.TCF','3D') # for now, it only read 3D RI data
print(f"number of snapshots : {len(tcfile)}")

## Usage 1: handling a data for each snapshot
data = tcfile[0]
print(f"shape of data : {data.shape}")
# or
for data in tcfile:
    # do some operations on the data ...
    pass

## Usage 2: Evaluate cell properties of each cell in a single snapshot
bgRI = 1.337 # refractive index of media
rtn_cellmask = False # check whether you store cell mask or not

def cotraints(tcfcell:TCFcell):
    if tcfcell.DMass > 30: # dry mass is more than 30
        return True
    return False
tcfcell_group = [get_celldata(tcfile, snapshot_number,bgRI, rtn_cellmask = rtn_cellmask) 
                    for snapshotnumber in range(len(tcfile))]
# save example
tcfcell = tcfcell_group[0][0]
tcfcell.save("tcfcell_0th_snapshot_0th_cell.h5")

# load example
tcfcell = TCFcell("tcfcell_0th_snapshot_0th_cell.h5")


## Usage 3: track each cell using positional parameters and save the parameter
tcfcell_t_group = get_celldata_t(tcfcells_tlapse)

# save example
tcfcell_t = tcfcell_t_group[0] 
tcfcell_t.save("tcfcell_0th_cell_tracking_result.h5")

# load example
tcfcell_t = TCFcell_t("tcfcell_0th_snapshot_0th_cell.h5")

```

## Test (for development and contribution)

```bash
pytest Tomocell/tests/TCFhandler.py
```
