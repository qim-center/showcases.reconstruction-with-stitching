import argparse
import src.cfg as cfg
from src.io import load_recon, save_recon

def downsample_recons(scans):
    factor = cfg.downsampled.factor
    for scan in scans:
        vol = load_recon(scan, dataset=cfg.full_res)
        vol = vol[::factor, ::factor, ::factor]
        save_recon(vol, scan, dataset=cfg.downsampled)

def main():
    parser = argparse.ArgumentParser(description='Downsampled reconstruction (downsampled dataset) of the padded reconstructions (full_res dataset).')
    parser.add_argument(
        '-s', '--scan',
        required=False, nargs='+',
        help='One or more scans to downsample. Omit to downsample all scans.'
    )
    args = parser.parse_args()

    if args.scan is None:
        scans = cfg.SCANS
    else:
        invalid = [s for s in args.scan if s not in cfg.SCANS]
        if invalid:
            raise ValueError(
                f"Unknown scan(s): {invalid}\n"
                f"Valid scans: {cfg.SCANS}"
            )
        scans = args.scan
    
    downsample_recons(scans)

if __name__ == '__main__':
    main()