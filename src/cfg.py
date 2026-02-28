import os
from dataclasses import dataclass
from pathlib import Path

SCAN_ROOT_ENV_KEY = 'SCAN_ROOT'
OUT_ROOT_ENV_KEY = 'OUT_ROOT'
DATASET_ENV_KEY = 'DATASET'

DEFAULT_DATASET = 'full_res'

def _required_env_path(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"{key} environment variable must be set")
    return Path(value)

SCAN_ROOT = _required_env_path(SCAN_ROOT_ENV_KEY)
OUT_ROOT = _required_env_path(OUT_ROOT_ENV_KEY)
RECON_ROOT = OUT_ROOT / 'recons'
STITCH_ROOT = OUT_ROOT / 'stitched'

SCANS_BY_LAYER = {
    4: ('top_4_1', 'top_4_2', 'top_4_3-ny', 'top_4_4'),
    3: ('top_3_1', 'top_3_2', 'top_3_3-ny', 'top_3_4'),
    2: ('top_2_1', 'top_2_2'),
    1: ('left_top_1',),
}
SCANS = tuple(s for l in SCANS_BY_LAYER.values() for s in l)

@dataclass(frozen=True)
class FullResDataset:
    name: str = 'full_res'
    recon_name: str = 'padded'
    ext: str = '.h5'
    h5_key: str = 'volume'
    factor: int = 1 # no downsampling

@dataclass(frozen=True)
class DownsampledDataset:
    name: str = 'downsampled'
    recon_name: str = 'padded_downsampled'
    ext: str = '.npy'
    factor: int = 3 # downsample factor in each axis

@dataclass(frozen=True)
class RawDataset:
    name: str = 'raw'
    recon_name: str = 'raw'
    ext: str = '.h5'
    h5_key: str = 'volume'
    factor: int = 1 # no downsampling

full_res = FullResDataset()
downsampled = DownsampledDataset()
raw = RawDataset()

_DATASETS = {
    'full_res': full_res,
    'downsampled': downsampled,
    'raw': raw,
}

for ds in _DATASETS.values():
    os.makedirs(RECON_ROOT / ds.recon_name, exist_ok=True)
    os.makedirs(STITCH_ROOT / 'volumes' / ds.name, exist_ok=True)
    os.makedirs(STITCH_ROOT / 'transforms' / ds.name, exist_ok=True)

DEFAULT_DATASET = 'full_res'
ENV_KEY = 'DATASET'

def _resolve_dataset(name: str):
    try:
        return _DATASETS[name]
    except KeyError:
        raise ValueError(
            f"{ENV_KEY} must be one of {tuple(_DATASETS)}, got {name!r}"
        )

def _dataset_from_env():
    name = os.getenv(ENV_KEY, DEFAULT_DATASET)
    return _resolve_dataset(name)

dataset = _dataset_from_env()

def set_dataset(name):
    global dataset
    dataset = _resolve_dataset(name)