import io

import numpy as np


def serialize(arr: np.ndarray) -> bytes:
    buf = io.BytesIO()
    np.savez_compressed(buf, predictions=arr.astype(np.float32))
    return buf.getvalue()


def deserialize(data: bytes) -> np.ndarray:
    buf = io.BytesIO(data)
    return np.load(buf)["predictions"]
