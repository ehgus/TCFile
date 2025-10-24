import json
import h5py
import numpy as np
from zarr.abc.store import Store
from typing import Optional, Iterator, Dict, List, Tuple, Any
from .TCFile_class import TCFileRI3D, TCFileFL3D


class TCFZarrStore(Store):
    """Read-only Zarr Store that exposes TCF (HDF5) datasets as OME-NGFF v0.4 compliant Zarr arrays.

    This store wraps TCFile classes (TCFileRI3D, TCFileFL3D) and provides a Zarr interface
    following the OME-NGFF v0.4 specification. Each image type is exposed as a separate
    group with appropriate multiscales metadata.

    Structure:
    - RI3D/: Refractive index 3D data as 4D array (TZYX)
    - FL3D/CH{n}/: Fluorescence 3D data, separate group per channel, 4D array (TZYX)

    Attributes
    ----------
    tcf_path : str
        Path to the TCF file
    available_groups : list[str]
        List of available Zarr groups

    Examples
    --------
    >>> store = TCFZarrStore('data.TCF')
    >>> print(store.available_groups)
    ['RI3D', 'FL3D/CH0', 'FL3D/CH1']
    >>> import zarr
    >>> root = zarr.group(store=store)
    >>> ri_array = root['RI3D/0']
    >>> print(ri_array.shape)  # (T, Z, Y, X)
    """

    def __init__(self, tcf_path: str):
        """Initialize TCFZarrStore.

        Parameters
        ----------
        tcf_path : str
            Path to the TCF file
        """
        self.tcf_path = tcf_path
        self._tcfiles: Dict[str, Any] = {}
        self._metadata_cache: Dict[str, bytes] = {}
        self.available_groups: List[str] = []

        # Detect and initialize available image types
        self._initialize_tcfiles()

        # Define chunk size (T, Z, Y, X)
        self._chunk_size = (1, 64, 256, 256)

    def _initialize_tcfiles(self):
        """Detect and initialize available TCFile instances."""
        # Try to open RI3D
        try:
            with h5py.File(self.tcf_path, 'r') as f:
                if '3D' in f.get('Data', {}):
                    self._tcfiles['RI3D'] = TCFileRI3D(self.tcf_path)
                    self.available_groups.append('RI3D')
        except Exception:
            pass

        # Try to open FL3D with all available channels
        try:
            with h5py.File(self.tcf_path, 'r') as f:
                if '3DFL' in f.get('Data', {}):
                    # Create first channel to get metadata
                    tcfile_fl = TCFileFL3D(self.tcf_path, channel=0)
                    max_channels = tcfile_fl.max_channels

                    # Initialize all channels
                    for ch in range(max_channels):
                        group_name = f'FL3D/CH{ch}'
                        self._tcfiles[group_name] = TCFileFL3D(self.tcf_path, channel=ch)
                        self.available_groups.append(group_name)
        except Exception:
            pass

        if not self.available_groups:
            raise ValueError(f'No supported image types found in {self.tcf_path}')

    def _get_tcfile(self, group_name: str):
        """Get TCFile instance for a group."""
        return self._tcfiles.get(group_name)

    def _parse_key(self, key: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[List[int]]]:
        """Parse Zarr key into components.

        Returns
        -------
        tuple
            (group_name, metadata_type, array_name, chunk_indices)
            - group_name: e.g., 'RI3D' or 'FL3D/CH0'
            - metadata_type: '.zgroup', '.zattrs', or None
            - array_name: e.g., '0' or None
            - chunk_indices: [t, z, y, x] or None
        """
        parts = key.split('/')

        # Root metadata
        if key in ['.zgroup', '.zattrs']:
            return (None, key, None, None)

        # Array metadata: RI3D/0/.zarray (check before group metadata)
        if len(parts) >= 3 and parts[-1] == '.zarray':
            group_name = '/'.join(parts[:-2])
            array_name = parts[-2]
            return (group_name, '.zarray', array_name, None)

        # Group metadata: RI3D/.zgroup or FL3D/CH0/.zattrs
        if parts[-1].startswith('.z'):
            group_name = '/'.join(parts[:-1])
            return (group_name, parts[-1], None, None)

        # Chunk data: RI3D/0/0.0.0.0 (t.z.y.x)
        if len(parts) >= 3 and '.' in parts[-1]:
            group_name = '/'.join(parts[:-2])
            array_name = parts[-2]
            chunk_indices = list(map(int, parts[-1].split('.')))
            return (group_name, None, array_name, chunk_indices)

        return (None, None, None, None)

    def _generate_root_metadata(self, meta_type: str) -> bytes:
        """Generate root-level metadata."""
        if meta_type == '.zgroup':
            return json.dumps({'zarr_format': 2}).encode()
        elif meta_type == '.zattrs':
            return json.dumps({}).encode()
        raise KeyError(meta_type)

    def _generate_group_metadata(self, group_name: str, meta_type: str) -> bytes:
        """Generate group-level metadata (.zgroup or .zattrs)."""
        tcfile = self._get_tcfile(group_name)
        if tcfile is None:
            raise KeyError(f'Group not found: {group_name}')

        if meta_type == '.zgroup':
            return json.dumps({'zarr_format': 2}).encode()

        elif meta_type == '.zattrs':
            # Generate OME-NGFF v0.4 multiscales metadata
            metadata = {
                'multiscales': [{
                    'version': '0.4',
                    'axes': [
                        {'name': 't', 'type': 'time', 'unit': 'second'},
                        {'name': 'z', 'type': 'space', 'unit': 'micrometer'},
                        {'name': 'y', 'type': 'space', 'unit': 'micrometer'},
                        {'name': 'x', 'type': 'space', 'unit': 'micrometer'}
                    ],
                    'datasets': [{
                        'path': '0',
                        'coordinateTransformations': [{
                            'type': 'scale',
                            'scale': [
                                float(tcfile.dt if tcfile.dt > 0 else 1.0),
                                float(tcfile.data_resolution[0]),
                                float(tcfile.data_resolution[1]),
                                float(tcfile.data_resolution[2])
                            ]
                        }]
                    }],
                    'name': group_name,
                    'type': 'none'
                }]
            }
            return json.dumps(metadata).encode()

        raise KeyError(meta_type)

    def _generate_array_metadata(self, group_name: str, array_name: str) -> bytes:
        """Generate array metadata (.zarray)."""
        if array_name != '0':
            raise KeyError(f'Only array "0" is supported, got: {array_name}')

        tcfile = self._get_tcfile(group_name)
        if tcfile is None:
            raise KeyError(f'Group not found: {group_name}')

        # Shape is (T, Z, Y, X) - convert to Python ints for JSON serialization
        shape = [int(len(tcfile))] + [int(s) for s in tcfile.data_shape]

        # Adjust chunk size to not exceed array dimensions
        chunks = [
            int(min(self._chunk_size[0], shape[0])),
            int(min(self._chunk_size[1], shape[1])),
            int(min(self._chunk_size[2], shape[2])),
            int(min(self._chunk_size[3], shape[3]))
        ]

        metadata = {
            'zarr_format': 2,
            'shape': shape,
            'chunks': chunks,
            'dtype': '<f4',
            'compressor': None,
            'fill_value': 0.0,
            'order': 'C',
            'filters': None
        }
        return json.dumps(metadata).encode()

    def _read_chunk(self, group_name: str, array_name: str, indices: List[int]) -> bytes:
        """Read chunk data and return as bytes.

        Parameters
        ----------
        group_name : str
            Group name (e.g., 'RI3D' or 'FL3D/CH0')
        array_name : str
            Array name (should be '0')
        indices : list[int]
            Chunk indices [t, z, y, x]

        Returns
        -------
        bytes
            Chunk data as bytes
        """
        if array_name != '0':
            raise KeyError(f'Only array "0" is supported')

        tcfile = self._get_tcfile(group_name)
        if tcfile is None:
            raise KeyError(f'Group not found: {group_name}')

        # Get chunk size and array shape
        shape = [len(tcfile)] + list(tcfile.data_shape)
        chunks = [
            min(self._chunk_size[0], shape[0]),
            min(self._chunk_size[1], shape[1]),
            min(self._chunk_size[2], shape[2]),
            min(self._chunk_size[3], shape[3])
        ]

        # Calculate slice ranges for this chunk
        t_idx, z_idx, y_idx, x_idx = indices

        t_start = t_idx * chunks[0]
        t_end = min(t_start + chunks[0], shape[0])
        z_start = z_idx * chunks[1]
        z_end = min(z_start + chunks[1], shape[1])
        y_start = y_idx * chunks[2]
        y_end = min(y_start + chunks[2], shape[2])
        x_start = x_idx * chunks[3]
        x_end = min(x_start + chunks[3], shape[3])

        # Allocate output array
        chunk_shape = (t_end - t_start, z_end - z_start, y_end - y_start, x_end - x_start)
        chunk_data = np.zeros(chunk_shape, dtype=np.float32)

        # Read time slices
        for t_offset, t in enumerate(range(t_start, t_end)):
            # Get full 3D volume for this timepoint
            volume_3d = tcfile[t]

            # Extract spatial chunk
            spatial_chunk = volume_3d[z_start:z_end, y_start:y_end, x_start:x_end]
            chunk_data[t_offset] = spatial_chunk

        return chunk_data.tobytes(order='C')

    # Zarr Store Protocol Implementation (v3 API)

    def get(self, key: str) -> Optional[bytes]:
        """Get item from store (Zarr v3 API).

        Parameters
        ----------
        key : str
            Zarr key (metadata or chunk)

        Returns
        -------
        bytes or None
            Data or metadata as bytes, or None if key doesn't exist
        """
        try:
            return self.__getitem__(key)
        except KeyError:
            return None

    def set(self, key: str, value: bytes):
        """Set item in store (not supported - read-only)."""
        raise PermissionError('TCFZarrStore is read-only')

    def delete(self, key: str):
        """Delete item from store (not supported - read-only)."""
        raise PermissionError('TCFZarrStore is read-only')

    def exists(self, key: str) -> bool:
        """Check if key exists in store."""
        try:
            self.__getitem__(key)
            return True
        except KeyError:
            return False

    def list(self) -> Iterator[str]:
        """List all keys in the store."""
        return iter(self)

    def list_prefix(self, prefix: str) -> Iterator[str]:
        """List keys with given prefix."""
        for key in self:
            if key.startswith(prefix):
                yield key

    def list_dir(self, prefix: str) -> Iterator[str]:
        """List direct children of a prefix."""
        if not prefix.endswith('/'):
            prefix = prefix + '/' if prefix else ''

        seen = set()
        for key in self:
            if key.startswith(prefix):
                remainder = key[len(prefix):]
                if '/' in remainder:
                    # Get the directory component
                    child = remainder.split('/')[0]
                    if child not in seen:
                        seen.add(child)
                        yield child
                elif remainder and remainder not in seen:
                    seen.add(remainder)
                    yield remainder

    def get_partial_values(self, key_ranges):
        """Get partial values (not implemented)."""
        raise NotImplementedError('get_partial_values is not supported')

    def supports_writes(self) -> bool:
        """Return whether store supports writes."""
        return False

    def supports_deletes(self) -> bool:
        """Return whether store supports deletes."""
        return False

    def supports_listing(self) -> bool:
        """Return whether store supports listing."""
        return True

    def __eq__(self, other):
        """Check equality."""
        if not isinstance(other, TCFZarrStore):
            return False
        return self.tcf_path == other.tcf_path

    # Dict-like interface for backwards compatibility

    def __getitem__(self, key: str) -> bytes:
        """Get item from store.

        Parameters
        ----------
        key : str
            Zarr key (metadata or chunk)

        Returns
        -------
        bytes
            Data or metadata as bytes
        """
        # Check cache first
        if key in self._metadata_cache:
            return self._metadata_cache[key]

        group_name, meta_type, array_name, chunk_indices = self._parse_key(key)

        # Root metadata
        if group_name is None and meta_type is not None:
            result = self._generate_root_metadata(meta_type)
            self._metadata_cache[key] = result
            return result

        # Group metadata
        if meta_type in ['.zgroup', '.zattrs']:
            result = self._generate_group_metadata(group_name, meta_type)
            self._metadata_cache[key] = result
            return result

        # Array metadata
        if meta_type == '.zarray':
            result = self._generate_array_metadata(group_name, array_name)
            self._metadata_cache[key] = result
            return result

        # Chunk data
        if chunk_indices is not None:
            return self._read_chunk(group_name, array_name, chunk_indices)

        raise KeyError(key)

    def __setitem__(self, key: str, value: bytes):
        """Set item in store (not supported - read-only)."""
        raise PermissionError('TCFZarrStore is read-only')

    def __delitem__(self, key: str):
        """Delete item from store (not supported - read-only)."""
        raise PermissionError('TCFZarrStore is read-only')

    def __contains__(self, key: str) -> bool:
        """Check if key exists in store."""
        return self.exists(key)

    def __iter__(self) -> Iterator[str]:
        """Iterate over all keys in the store."""
        # Root metadata
        yield '.zgroup'
        yield '.zattrs'

        # For each group
        for group_name in self.available_groups:
            # Group metadata
            yield f'{group_name}/.zgroup'
            yield f'{group_name}/.zattrs'

            # Array metadata
            yield f'{group_name}/0/.zarray'

            # Chunk keys
            tcfile = self._get_tcfile(group_name)
            if tcfile is not None:
                shape = [len(tcfile)] + list(tcfile.data_shape)
                chunks = [
                    min(self._chunk_size[0], shape[0]),
                    min(self._chunk_size[1], shape[1]),
                    min(self._chunk_size[2], shape[2]),
                    min(self._chunk_size[3], shape[3])
                ]

                # Calculate number of chunks in each dimension
                n_chunks = [
                    (shape[i] + chunks[i] - 1) // chunks[i]
                    for i in range(4)
                ]

                # Generate all chunk keys
                for t in range(n_chunks[0]):
                    for z in range(n_chunks[1]):
                        for y in range(n_chunks[2]):
                            for x in range(n_chunks[3]):
                                yield f'{group_name}/0/{t}.{z}.{y}.{x}'

    def __len__(self) -> int:
        """Return the number of keys in the store."""
        return sum(1 for _ in self)

    def keys(self) -> Iterator[str]:
        """Return iterator over keys."""
        return iter(self)

    def close(self):
        """Close all open file handles."""
        # TCFile instances open/close HDF5 files per access, so no persistent handles to close
        self._tcfiles.clear()
        self._metadata_cache.clear()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

    def list_groups(self) -> List[str]:
        """List available groups in the store.

        Returns
        -------
        list[str]
            List of group names
        """
        return self.available_groups.copy()
