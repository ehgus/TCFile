from typing import Sequence
from PIL import Image
import numpy as np
import h5py
import warnings
import hdf5plugin
import re

def TCFile(tcfname:str, imgtype):
    if imgtype == '3D':
        return TCFileRI3D(tcfname)
    if imgtype == '2DMIP':
        return TCFileRI2DMIP(tcfname)
    if imgtype == 'BF':
        return TCFileBF(tcfname)
    if imgtype == '3DFL':
        return TCFileFL3D(tcfname)
    ValueError('Unsupported imgtype: Supported imgtypes are "3D","2DMIP", and "BF"')

class TCFileAbstract(Sequence):
    '''
    interface class to TCF files.
    This class returns data as if list containg multiple data.
    Preview of the data is stored in attributes.
    * Note: It can read 3D, 2DMIP, and BF. 

    Attributes
    ----------
    format_version : str
    length : int
        time series length of the TCF file
    data_shape : numpy.array[int]
        shape of single shot data
    data_resolution : numpy.array[float]
        (unit: μm) resolution of data. It represents unit resolution per pixel
    dt : float
        (unit: s) Time steps of data. Zero if it is single shot data
    tcfname : str
    '''
    imgtype = None
    data_ndim = None

    def __init__(self, tcfname:str):
        '''
        Paramters
        ---------
        tcfname : str
            location of the target TCF file

        Raises
        ------
        ValueError
            If imgtype is unsupported given tcf file.
        '''
        assert isinstance(self.imgtype, str), 'imgtype should be specified by maintainer. Contact authors'
        assert isinstance(self.data_ndim, int), 'data_ndim should be specified by maintainer. Contact authors'

        self.tcfname = tcfname
        with h5py.File(tcfname) as tcf_io:
            assert 'Data' in tcf_io, 'The given file is not TCF file'
            assert self.imgtype in tcf_io['Data'], 'The current imgtype is not supported in this file'
            # load attributes
            self.format_version = self.get_attr(tcf_io, '/', 'FormatVersion')
            if not isinstance(self.format_version, str):
                self.format_version = self.format_version.decode('UTF-8')

            data_info_path = f'/Data/{self.imgtype}'
            get_data_info_attr = lambda attr_name: self.get_attr(tcf_io, data_info_path, attr_name, default = 0)

            self.data_shape = list(get_data_info_attr(f'Size{axis}') for axis in  ('Z', 'Y', 'X')[3-self.data_ndim:])
            self.data_resolution = list(get_data_info_attr(f'Resolution{axis}') for axis in  ('Z', 'Y', 'X')[3-self.data_ndim:])
            self.length = get_data_info_attr('DataCount')
            self.dt = 0 if self.length == 1 else get_data_info_attr('DataCount')

    def copy(self, output_file_path, compression_opt = {}):
        """
        Copies the structure, data, and attributes of an HDF5 file to a new file, compressing all datasets using gzip.

        Parameters:
        - input_file_path: path to the input HDF5 file.
        - output_file_path: path where the output HDF5 file will be created.
        - compression_opt: Type of compression to use. default is uncompress data.
            If you want to compress data using gzip type `{"compression":"gzip", "compression_opts":}`.
        
        Note: This function does not return anything.
        """
        def copy_attributes(source, destination):
            """
            Copies attributes from the source to the destination.
            """
            for attr_name in source.attrs:
                destination.attrs[attr_name] = source.attrs[attr_name]

        def recursively_copy_and_compress(group_in, group_out):
            """
            Recursively copies groups/datasets from the input file to the output file with compression and copies attributes.
            """
            copy_attributes(group_in, group_out)  # Copy attributes for the group

            for key in group_in:
                item_in = group_in[key]
                if isinstance(item_in, h5py.Dataset):
                    # Copy dataset with compression and its attributes
                    data = item_in[...]
                    dataset_out = group_out.create_dataset(key, data=data, **compression_opt)
                    copy_attributes(item_in, dataset_out)  # Copy attributes for the dataset
                elif isinstance(item_in, h5py.Group):
                    # Create group in the output file, copy attributes, and recurse
                    group_out_sub = group_out.create_group(key)
                    recursively_copy_and_compress(item_in, group_out_sub)

        with h5py.File(self.tcfname, 'r') as file_in:
            with h5py.File(output_file_path, 'w') as file_out:
                recursively_copy_and_compress(file_in, file_out)

    def __len__(self):
        '''
        Return the number of images available. 
        '''
        return self.length

    def __getitem__(self, key:int) -> np.ndarray:
        '''
        Return
        ------
        data : numpy.ndarray[uint8]
            return a single image.

        Raises
        ------
        TypeError
            If key is not int
        IndexError
            If key is out of bound
        '''
        data_path = self.get_data_location(key)
        # FILL THIS AREA: find raw data in data_path and process them into a desired format
        NotImplementedError('__getitem__ should not implemented')

    def get_data_location(self, key:int) -> str:
        '''
        Return
        ------
        data_location: str
            return the path of data corresponding to key
            It checks whether the key is defined corretly
        '''
        length = len(self)
        if not isinstance(key, int):
            raise TypeError(f'{self.__class__} indices must be integer, not {type(key)}')
        if key < -length or key >= length:
            raise IndexError(f'{self.__class__} index out of range')
        key = (key + length) % length
        data_path = f'/Data/{self.imgtype}/{key:06d}'
        return data_path
    
    @staticmethod
    def get_attr(tcf_io, path, attr_name, default = None):
        attr_value = tcf_io[path].attrs.get(attr_name, default = [default])[0]
        return attr_value

class TCFileRIAbstract(TCFileAbstract):
    def __getitem__(self, key: int) -> np.ndarray:
        data_path = self.get_data_location(key)
        with h5py.File(self.tcfname) as tcf_io:
            get_data_attr = lambda attr_name: self.get_attr(tcf_io, data_path, attr_name)
            if self.format_version < '1.3':
                # RI = data
                data = tcf_io[data_path][()]
            else:
                try:
                    # RI = data/1e4
                    data = tcf_io[data_path][()]
                    data = data.astype(np.float32)
                    data /= 1e4
                except:
                    warnings.warn(("You use an experimental file format deprecated.\n"
                                   "Update your reconstruction program and rebuild TCF file."))
                    # RI = data/1e3 + min_RI for uint8 data type (ScalarType True)
                    # RI = data/1e4          for uint16 data type (ScalarType False)
                    is_uint8 = get_data_attr('ScalarType')
                    if is_uint8:
                        data_type = np.uint8
                    else:
                        data_type = np.uint16
                    data = np.zeros(self.data_shape, data_type)

                    tile_count = get_data_attr('NumberOfTiles')
                    tile_path_list = [ p for p in tcf_io.keys() if re.match(r'^TILE_\d+$', p)]
                    tile_path_list.sort()
                    for p in tile_path_list:
                        tile_path = f'{data_path}/{p}'
                        get_tile_attr = lambda attr_name: self.get_attr(tcf_io, tile_path, attr_name)
                        sampling_step = get_tile_attr('SamplingStep')
                        if sampling_step != 1:
                            # what?! I don't know why... ask Tomocube
                            continue

                        offset = list(get_tile_attr(f'DataIndexOffsetPoint{axis}') for axis in ('Z', 'Y', 'X')[3-self.data_ndim:])
                        last_idx = list(get_tile_attr(f'DataIndexLastPoint{axis}') for axis in ('Z', 'Y', 'X')[3-self.data_ndim:])
                        mapping_range = tuple(slice(start,end + 1) for start, end in zip(offset, last_idx))
                        valid_data_range = tuple(slice(0,end - start + 1) for start, end in zip(offset, last_idx))
                        data[mapping_range] += tcf_io[tile_path][valid_data_range]
                    data = data.astype(np.float32)
                    if is_uint8:
                        min_RI = get_data_attr('RIMin')
                        data /= 1e3
                        data += min_RI
                    else:
                        data /= 1e4

        return data

class TCFileRI3D(TCFileRIAbstract):
    imgtype = '3D'
    data_ndim = 3

class TCFileRI2DMIP(TCFileRIAbstract):
    imgtype = '2DMIP'
    data_ndim = 2

class TCFileBF(TCFileAbstract):
    imgtype = 'BF'
    data_ndim = 2
    def __getitem__(self, key: int) -> np.ndarray:
        data_path = self.get_data_location(key)
        with h5py.File(self.tcfname) as f:
            data = f[data_path][()]
        data = Image.fromarray(data, mode = 'RGB')
        return data

class TCFileFL3D(TCFileAbstract):
    imgtype = '3DFL'
    data_ndim = 3
    channel = 0
    def __init__(self, tcfname: str):
        super().__init__(tcfname)
        with h5py.File(self.tcfname) as f:
            self.max_channels = self.get_attr(f, f'/Data/{self.imgtype}', 'Channels')

    def __getitem__(self, key: int) -> np.ndarray:
        self.imgtype = f'3DFL/CH{self.channel}'
        data_path = self.get_data_location(key)
        self.imgtype = '3DFL'
        with h5py.File(self.tcfname) as f:
            data = f[data_path][()]
        return data

