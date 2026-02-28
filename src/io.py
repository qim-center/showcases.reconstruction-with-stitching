import numpy as np
import h5py
from pathlib import Path
import src.cfg as cfg

def load_recon(scan_name, dataset=None):
    ds = cfg.dataset if dataset is None else dataset

    path = cfg.RECON_ROOT / ds.recon_name / (scan_name + ds.ext)
    if ds.ext == '.h5':
        with h5py.File(path, 'r') as f:
            vol = f[ds.h5_key][()]
    elif ds.ext == '.npy':
        vol = np.load(path)
    else:
        raise ValueError
    
    return vol

def load_recons(scan_names, dataset=None):
    ds = cfg.dataset if dataset is None else dataset

    vols = [load_recon(scan, dataset=ds) for scan in scan_names]
    return np.stack(vols, axis=0)

def save_recon(vol: np.ndarray, scan_name, dataset=None):
    ds = cfg.dataset if dataset is None else dataset

    path = cfg.RECON_ROOT / ds.recon_name / (scan_name + ds.ext)
    if ds.name in ['full_res', 'raw']:
        with h5py.File(path, 'w') as f:
            f.create_dataset(ds.h5_key, data=vol, compression='gzip')
    elif ds.name == 'downsampled':
        np.save(path, vol)
    else:
        raise ValueError
    
    print(f"Wrote recon: {path} with shape {vol.shape}")

def save_stitch(vol: np.ndarray, step_name: str):
    ds = cfg.dataset

    path = cfg.STITCH_ROOT / 'volumes' / ds.name / (step_name + ds.ext)
    if ds.name == 'full_res':
        with h5py.File(path, 'w') as f:
            f.create_dataset(ds.h5_key, data=vol, compression='gzip')
    elif ds.name == 'downsampled':
        np.save(path, vol)
    else:
        raise ValueError

    print(f"Wrote stitch: {path} with shape {vol.shape}")

def load_stitch(step_name: str):
    ds = cfg.dataset

    path = cfg.STITCH_ROOT / 'volumes' / ds.name / (step_name + ds.ext)
    if ds.name == 'full_res':
        with h5py.File(path, 'r') as f:
            vol = f[ds.h5_key][()]
        return vol
    elif ds.name == 'downsampled':
        return np.load(path)
    
    raise ValueError

def save_transform(A_hom: np.ndarray, step_name: str):
    path = cfg.STITCH_ROOT / 'transforms' / cfg.dataset.name / f'{step_name}.npy'
    np.save(path, A_hom)

def load_transform(step_name: str, dataset=None):
    ds = cfg.dataset if dataset is None else dataset

    path = cfg.STITCH_ROOT / 'transforms' / ds.name / f'{step_name}.npy'
    return np.load(path)

def load_layer(layer: int, indices: tuple[int, ...] | None = None, grid: bool = False):
    """
    Load scans for a given layer.

    grid:
        If True, assemble volumes into the proper grid in the arrangement it was acquired in.
        If False, stack the volumes.
    """
    if layer not in cfg.SCANS_BY_LAYER:
        raise ValueError(f"Unknown layer {layer}")
    
    if grid and indices is not None:
        raise ValueError("indices is only supported when grid=False")
    
    scans = cfg.SCANS_BY_LAYER[layer]
    
    if indices is not None:
        scans = [scans[i] for i in indices]

    vols = load_recons(scans)

    if not grid:
        return vols
    
    if layer in (4, 3):
        # Layout:
        #   [2 3]
        #   [1 0]
        top = np.concatenate([vols[2], vols[3]], axis=2)
        bottom = np.concatenate([vols[1], vols[0]], axis=2)
        return np.concatenate([top, bottom], axis=1)
    
    if layer == 2:
        return np.concatenate([vols[1], vols[0]], axis=1)
    
    if layer == 1:
        return vols[0]
    
    return ValueError
