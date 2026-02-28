import src.cfg as cfg
from src.io import load_recon, save_recon

factor = cfg.downsampled.factor
for scan in cfg.SCANS:
    vol = load_recon(scan, dataset=cfg.full_res)
    vol = vol[::factor, ::factor, ::factor]
    save_recon(vol, scan, dataset=cfg.downsampled)