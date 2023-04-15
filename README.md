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

## Usage 1: handling each snapshots (or data)
data = tcfile[0]
print(f"shape of data : {data.shape}")
# or
for data in tcfile:
    # do some operations on the data ...
    pass
```

## TODO

- [ ] fluorescence data reader
- [ ] TCFile compressor/decompressor for portability
- [ ] rich documentation
- [ ] rigorous tests
- [ ] TCFile writer ?
- [ ] TCFile converter ?

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
