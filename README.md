# TCFile python package

A basic image processing tool of tomocube data.

## Installation

```bash
pip install TCFile
```

## Use case

```python

from TCFile import TCFile

tcfile = TCFile('test.TCF','3D') # ready for return 3D RI images
print(f"number of snapshots : {len(tcfile)}")

## Usage 1: handling each snapshots (numpy array)
data = tcfile[0]
print(f"shape of data : {data.shape}")
# or
for data in tcfile:
    # do some operations on the data ...
    pass

## Usage 2: handling fluorescence array
tcfile_fl = TCFile('test.TCF','3DFL')
fl_data = tcfile_fl[0]

## Usage 2: handling dask array
data = tcfile.asdask() # (T, Z, Y, X) array

```

## Limitation

It does not support TCF writer due to the difficulty of configuring metadata and interoperability with commercial Tomocube software.

## TODO
- [ ] rigorous tests
- [ ] TCFile converter

Any suggestions and comments are welcome!

## Test

```bash
# install this package in editable mode
git clone https://github.com/ehgus/TCFile.git
cd TCFile
pip install -e .
# execute pytest
pytest
```
