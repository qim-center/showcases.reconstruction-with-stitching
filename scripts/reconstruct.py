import argparse
import src.cfg as cfg
from src.scan_index import list_scan_configs, get_xtekct_path
from src.ct import read_and_process, reconstruct_with_padding, reconstruct
from src.io import save_recon

def reconstruct_scans(scans):
    ds = cfg.dataset

    if ds.name not in ['full_res', 'raw']:
        raise ValueError

    for scan in scans:
        confs = list_scan_configs(scan)
        recon_confs = [c for c in confs if '_recon' in c]
        assert len(recon_confs) == 1
        xtekct_path = get_xtekct_path(scan, recon_confs[0])
        
        print(f"{scan}: reading and processing")
        ct_data = read_and_process(file_name=xtekct_path)

        print(f"{scan}: reconstructing with padding")

        if ds.name == 'full_res':
            recon = reconstruct_with_padding(data=ct_data, pad_factor=0.25).array
        elif ds.name == 'raw':
            recon = reconstruct(data=ct_data).array
        else:
            raise ValueError

        save_recon(recon, scan)
        
        print(f"{scan}: done")

def main():
    parser = argparse.ArgumentParser(description='Reconstruct with either padding (full_res dataset) or no padding (raw dataset).')
    parser.add_argument(
        '-s', '--scan',
        required=False, nargs='+',
        help='One or more scans to reconstruct. Omit to reconstruct all scans.'
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
    
    reconstruct_scans(scans)

if __name__ == '__main__':
    main()