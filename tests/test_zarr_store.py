import json
import pytest
import numpy as np
from TCFile import TCFZarrStore
from . import SAMPLE_TCF_FILE


class TestTCFZarrStore:
    """Test suite for TCFZarrStore class."""

    def test_store_initialization(self):
        """Test that store initializes correctly."""
        store = TCFZarrStore(SAMPLE_TCF_FILE)
        assert store.tcf_path == SAMPLE_TCF_FILE
        assert len(store.available_groups) > 0
        assert 'RI3D' in store.available_groups or any('FL3D' in g for g in store.available_groups)

    def test_store_context_manager(self):
        """Test that store works as context manager."""
        with TCFZarrStore(SAMPLE_TCF_FILE) as store:
            assert store is not None
            assert len(store.available_groups) > 0

    def test_root_metadata(self):
        """Test root-level metadata generation."""
        store = TCFZarrStore(SAMPLE_TCF_FILE)

        # Test .zgroup
        zgroup = store['.zgroup']
        assert isinstance(zgroup, bytes)
        zgroup_dict = json.loads(zgroup)
        assert zgroup_dict['zarr_format'] == 2

        # Test .zattrs
        zattrs = store['.zattrs']
        assert isinstance(zattrs, bytes)
        zattrs_dict = json.loads(zattrs)
        assert isinstance(zattrs_dict, dict)

    def test_group_metadata(self):
        """Test group-level metadata for available groups."""
        store = TCFZarrStore(SAMPLE_TCF_FILE)

        for group_name in store.available_groups:
            # Test .zgroup
            zgroup = store[f'{group_name}/.zgroup']
            assert isinstance(zgroup, bytes)
            zgroup_dict = json.loads(zgroup)
            assert zgroup_dict['zarr_format'] == 2

            # Test .zattrs (OME-NGFF metadata)
            zattrs = store[f'{group_name}/.zattrs']
            assert isinstance(zattrs, bytes)
            zattrs_dict = json.loads(zattrs)
            assert 'multiscales' in zattrs_dict
            assert isinstance(zattrs_dict['multiscales'], list)
            assert len(zattrs_dict['multiscales']) > 0

            # Validate OME-NGFF v0.4 structure
            ms = zattrs_dict['multiscales'][0]
            assert ms['version'] == '0.4'
            assert 'axes' in ms
            assert 'datasets' in ms
            assert 'name' in ms

            # Check axes
            axes = ms['axes']
            assert len(axes) == 4  # TZYX
            assert axes[0]['name'] == 't'
            assert axes[0]['type'] == 'time'
            assert axes[1]['name'] == 'z'
            assert axes[1]['type'] == 'space'
            assert axes[2]['name'] == 'y'
            assert axes[2]['type'] == 'space'
            assert axes[3]['name'] == 'x'
            assert axes[3]['type'] == 'space'

            # Check datasets
            datasets = ms['datasets']
            assert len(datasets) == 1  # Single resolution
            assert datasets[0]['path'] == '0'
            assert 'coordinateTransformations' in datasets[0]

            # Check coordinate transformations
            transforms = datasets[0]['coordinateTransformations']
            assert len(transforms) == 1
            assert transforms[0]['type'] == 'scale'
            assert 'scale' in transforms[0]
            assert len(transforms[0]['scale']) == 4  # TZYX

    def test_array_metadata(self):
        """Test array-level metadata (.zarray)."""
        store = TCFZarrStore(SAMPLE_TCF_FILE)

        for group_name in store.available_groups:
            zarray = store[f'{group_name}/0/.zarray']
            assert isinstance(zarray, bytes)
            zarray_dict = json.loads(zarray)

            # Check required fields
            assert zarray_dict['zarr_format'] == 2
            assert 'shape' in zarray_dict
            assert 'chunks' in zarray_dict
            assert 'dtype' in zarray_dict
            assert zarray_dict['dtype'] == '<f4'
            assert zarray_dict['order'] == 'C'

            # Check shape is 4D (TZYX)
            shape = zarray_dict['shape']
            assert len(shape) == 4
            assert all(s > 0 for s in shape)

            # Check chunks don't exceed shape
            chunks = zarray_dict['chunks']
            assert len(chunks) == 4
            for i in range(4):
                assert chunks[i] <= shape[i]

    def test_chunk_reading(self):
        """Test reading chunk data."""
        store = TCFZarrStore(SAMPLE_TCF_FILE)

        for group_name in store.available_groups:
            # Get array metadata to know shape and chunks
            zarray = json.loads(store[f'{group_name}/0/.zarray'])
            shape = zarray['shape']
            chunks = zarray['chunks']

            # Read first chunk (0.0.0.0)
            chunk_key = f'{group_name}/0/0.0.0.0'
            chunk_data = store[chunk_key]
            assert isinstance(chunk_data, bytes)

            # Calculate expected chunk size
            chunk_shape = [min(chunks[i], shape[i]) for i in range(4)]
            expected_size = np.prod(chunk_shape) * 4  # float32 = 4 bytes
            assert len(chunk_data) == expected_size

            # Verify we can decode it
            decoded = np.frombuffer(chunk_data, dtype=np.float32)
            assert decoded.shape[0] == np.prod(chunk_shape)

    def test_key_parsing(self):
        """Test key parsing functionality."""
        store = TCFZarrStore(SAMPLE_TCF_FILE)

        # Test root metadata
        group, meta, array, indices = store._parse_key('.zgroup')
        assert group is None
        assert meta == '.zgroup'
        assert array is None
        assert indices is None

        # Test group metadata
        group, meta, array, indices = store._parse_key('RI3D/.zattrs')
        assert group == 'RI3D'
        assert meta == '.zattrs'
        assert array is None
        assert indices is None

        # Test array metadata
        group, meta, array, indices = store._parse_key('RI3D/0/.zarray')
        assert group == 'RI3D'
        assert meta == '.zarray'
        assert array == '0'
        assert indices is None

        # Test chunk key
        group, meta, array, indices = store._parse_key('RI3D/0/1.2.3.4')
        assert group == 'RI3D'
        assert meta is None
        assert array == '0'
        assert indices == [1, 2, 3, 4]

        # Test FL3D group parsing
        if any('FL3D' in g for g in store.available_groups):
            group, meta, array, indices = store._parse_key('FL3D/CH0/.zattrs')
            assert group == 'FL3D/CH0'
            assert meta == '.zattrs'

    def test_store_contains(self):
        """Test __contains__ method."""
        store = TCFZarrStore(SAMPLE_TCF_FILE)

        # Root metadata should exist
        assert '.zgroup' in store
        assert '.zattrs' in store

        # Group metadata should exist
        for group_name in store.available_groups:
            assert f'{group_name}/.zgroup' in store
            assert f'{group_name}/.zattrs' in store
            assert f'{group_name}/0/.zarray' in store

        # Invalid keys should not exist
        assert 'nonexistent' not in store
        assert 'RI3D/999/.zarray' not in store

    def test_store_iteration(self):
        """Test that store can be iterated."""
        store = TCFZarrStore(SAMPLE_TCF_FILE)

        keys = list(store)
        assert len(keys) > 0

        # Check that root metadata is present
        assert '.zgroup' in keys
        assert '.zattrs' in keys

        # Check that group metadata is present
        for group_name in store.available_groups:
            assert f'{group_name}/.zgroup' in keys
            assert f'{group_name}/.zattrs' in keys
            assert f'{group_name}/0/.zarray' in keys

    def test_store_read_only(self):
        """Test that store is read-only."""
        store = TCFZarrStore(SAMPLE_TCF_FILE)

        # __setitem__ should raise PermissionError
        with pytest.raises(PermissionError):
            store['test_key'] = b'test_value'

        # __delitem__ should raise PermissionError
        with pytest.raises(PermissionError):
            del store['.zgroup']

    def test_list_groups(self):
        """Test list_groups method."""
        store = TCFZarrStore(SAMPLE_TCF_FILE)

        groups = store.list_groups()
        assert isinstance(groups, list)
        assert len(groups) > 0

        # Should contain RI3D or FL3D groups
        assert 'RI3D' in groups or any('FL3D' in g for g in groups)

    def test_metadata_caching(self):
        """Test that metadata is cached."""
        store = TCFZarrStore(SAMPLE_TCF_FILE)

        # Access metadata twice
        metadata1 = store['.zgroup']
        metadata2 = store['.zgroup']

        # Should be the same object (cached)
        assert metadata1 is metadata2

    def test_chunk_data_consistency(self):
        """Test that chunk data matches TCFile data."""
        store = TCFZarrStore(SAMPLE_TCF_FILE)

        # Get first available group
        group_name = store.available_groups[0]

        # Get array metadata
        zarray = json.loads(store[f'{group_name}/0/.zarray'])
        shape = zarray['shape']
        chunks = zarray['chunks']

        # Read first chunk
        chunk_data = store[f'{group_name}/0/0.0.0.0']
        chunk_array = np.frombuffer(chunk_data, dtype=np.float32)

        # Reshape to 4D
        chunk_shape = [min(chunks[i], shape[i]) for i in range(4)]
        chunk_array = chunk_array.reshape(chunk_shape)

        # Get corresponding data from TCFile
        tcfile = store._get_tcfile(group_name)
        if tcfile is not None:
            # Get first timepoint
            tcfile_data = tcfile[0]

            # Extract corresponding spatial region
            z_end = min(chunks[1], shape[1])
            y_end = min(chunks[2], shape[2])
            x_end = min(chunks[3], shape[3])

            expected_data = tcfile_data[:z_end, :y_end, :x_end]

            # Compare
            np.testing.assert_array_equal(chunk_array[0], expected_data)

    def test_invalid_array_name(self):
        """Test that invalid array names raise KeyError."""
        store = TCFZarrStore(SAMPLE_TCF_FILE)

        group_name = store.available_groups[0]

        # Only array "0" is supported
        with pytest.raises(KeyError):
            store[f'{group_name}/1/.zarray']

    def test_close_method(self):
        """Test that close method works."""
        store = TCFZarrStore(SAMPLE_TCF_FILE)

        # Verify store works before close
        assert '.zgroup' in store

        # Close the store
        store.close()

        # After close, internal structures should be cleared
        assert len(store._tcfiles) == 0
        assert len(store._metadata_cache) == 0
