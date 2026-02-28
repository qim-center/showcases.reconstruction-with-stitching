import os
import pathlib
import argparse
import src.cfg as cfg

_SCAN_ROOT = cfg.SCAN_ROOT

def get_xtekct_path(scan, config):
    base = _SCAN_ROOT
    subfolder = ''
    for f in os.listdir(base):
        if scan in f:
            subfolder = f
            break
    if not subfolder:
        raise ValueError('Could not find scan.')
    
    xtekct_file = os.path.join(base, f'{subfolder}/{config}.xtekct')
    return xtekct_file

def list_Casper_scans():
    base = _SCAN_ROOT
    scans = []
    for f in os.listdir(base):
        scans.append(f.split(' ')[0].split('_', 1)[1])
    scans.sort()
    return scans

def list_scan_configs(scan):
    base = _SCAN_ROOT
    recons = []
    for f in os.listdir(base):
        if scan in f:
            subfolder = f
            break
    for xtekct_path in pathlib.Path(base, subfolder).glob('*.xtekct'):
        recons.append(xtekct_path.stem)
    recons.sort()
    return recons

def get_xtekct_path_CLI(scan=None, config=None):
    scans = list_Casper_scans()
    if scan is None:
        print("No scan chosen. Choose by name from:")
        print(scans)
        return
    
    if scan not in scans:
        print("Invalid scan name. Choose by name from:")
        print(scans)
        return
    
    configs = list_scan_configs(scan)
    if config is None:
        print("No config chosen. Choose by index from:")
        print(configs)
        return
    
    try:
        config = configs[config]
    except IndexError:
        print('Invalid configuration index. Choose by index from:')
        print(configs)
        return
    
    return get_xtekct_path(scan, config)

def main():
    parser = argparse.ArgumentParser(description='Retrieve xtekct path for a specific Casper scan.')
    parser.add_argument('-s', '--scan', required=False, help='Scan to use. Omit to see available scans.')
    parser.add_argument('-c', '--config', type=int, required=False, help='Config to use from the scan. Chosen by index of the output of calling with --scan alone.')
    args = parser.parse_args()

    xtekct_path = get_xtekct_path_CLI(args.scan, args.config)
    if xtekct_path:
        print(xtekct_path)

if __name__ == '__main__':
    main()