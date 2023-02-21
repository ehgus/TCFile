## TCFile python package

Basic image processing tools of tomocube data.

## Installation

After downloading the repository, execute the following command in the repository;

```bash
pip install .
```

## Note

It is not for normal users, and API is not fixed. 
Please use this package with full understanding.
Any suggestions and comments are welcome! 

## Use case

```python

from TCFile import *

tcfile = TCFile('test.TCF','3D') # for now, it only read 3D RI data
print(f"number of snapshots : {len(tcfile)}")

## Usage 1: handling a data for each snapshot
data = tcfile[0]
print(f"shape of data : {data.shape}")
# or
for data in tcfile:
    # do some operations on the data ...
    pass
```

## Test (for development and contribution)

```bash
pytest TCFile/tests/TCFhandler.py
```
