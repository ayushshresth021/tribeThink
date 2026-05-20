import numpy as np
import pytest

from workers.predictions import deserialize, serialize


def test_roundtrip_preserves_shape_and_values():
    arr = np.random.rand(30, 20484).astype(np.float32)
    assert np.array_equal(deserialize(serialize(arr)), arr)


def test_roundtrip_preserves_float32_dtype():
    arr = np.ones((10, 20484), dtype=np.float32)
    assert deserialize(serialize(arr)).dtype == np.float32


def test_serialize_produces_bytes():
    arr = np.zeros((5, 20484), dtype=np.float32)
    assert isinstance(serialize(arr), bytes)


def test_roundtrip_single_timestep():
    arr = np.random.rand(1, 20484).astype(np.float32)
    result = deserialize(serialize(arr))
    assert result.shape == (1, 20484)
    assert np.array_equal(result, arr)
