import sys
import time
import numpy as np

import src.cfg as cfg
from src.volume_stitcher import estimate_transform, stitch
from src.io import load_layer, save_stitch, load_stitch, save_transform, load_transform
from src.utils import timed

scale = int(cfg.downsampled.factor / cfg.dataset.factor)

def get_transform(step_name, vol_fixed, vol_moving, **kwargs):
    if cfg.dataset.name == 'raw':
        A_hom = load_transform(step_name, cfg.full_res)
    else:
        A_hom = estimate_transform(vol_fixed, vol_moving, **kwargs)
    
    return A_hom

def step_4_10():
    step_name = 'top_4_10'

    with timed('load_layer'):
        vol_fixed, vol_moving = load_layer(4, (1, 0))

    with timed('get_transform'):
        A_hom = get_transform(step_name, vol_fixed, vol_moving)

    with timed('stitch'):
        vol_stitched = stitch(vol_fixed, vol_moving, A_hom)

    save_transform(A_hom, step_name)

    with timed('save_stitch'):
        save_stitch(vol_stitched, step_name)

def step_4_23():
    step_name = 'top_4_23'
    vol_fixed, vol_moving = load_layer(4, (2, 3))
    A_hom = get_transform(step_name, vol_fixed, vol_moving)
    vol_stitched = stitch(vol_fixed, vol_moving, A_hom)
    save_transform(A_hom, step_name)
    save_stitch(vol_stitched, step_name)

def step_4():
    step_name = 'top_4'
    vol_fixed = load_stitch('top_4_23')
    vol_moving = load_stitch('top_4_10')

    mask_fixed = np.zeros(vol_fixed.shape, dtype=bool)
    mask_fixed[:,int(0.5*vol_fixed.shape[1]):,:] = 1
    mask_moving = np.zeros(vol_moving.shape, dtype=bool)
    mask_moving[:,:int(0.5*vol_moving.shape[1]),:] = 1

    A_hom = get_transform(step_name, vol_fixed*mask_fixed, vol_moving*mask_moving)
    vol_stitched = stitch(vol_fixed, vol_moving, A_hom)
    save_transform(A_hom, step_name)
    save_stitch(vol_stitched, step_name)

def step_3_10():
    step_name = 'top_3_10'
    vol_fixed, vol_moving = load_layer(3, (1, 0))
    A_hom = get_transform(step_name, vol_fixed, vol_moving)
    vol_stitched = stitch(vol_fixed, vol_moving, A_hom)
    save_transform(A_hom, step_name)
    save_stitch(vol_stitched, step_name)

def step_3_23():
    step_name = 'top_3_23'
    vol_fixed, vol_moving = load_layer(3, (2, 3))
    A_hom = get_transform(step_name, vol_fixed, vol_moving)
    vol_stitched = stitch(vol_fixed, vol_moving, A_hom)
    save_transform(A_hom, step_name)
    save_stitch(vol_stitched, step_name)

def step_3():
    step_name = 'top_3'
    vol_fixed = load_stitch('top_3_23')
    vol_moving = load_stitch('top_3_10')
    
    mask_fixed = np.zeros(vol_fixed.shape, dtype=bool)
    mask_fixed[:,int(0.5*vol_fixed.shape[1]):,:] = 1
    mask_moving = np.zeros(vol_moving.shape, dtype=bool)
    mask_moving[:,:int(0.5*vol_moving.shape[1]),:] = 1

    A_hom = get_transform(step_name, vol_fixed*mask_fixed, vol_moving*mask_moving)
    vol_stitched = stitch(vol_fixed, vol_moving, A_hom)
    save_transform(A_hom, step_name)
    save_stitch(vol_stitched, step_name)

def step_2():
    step_name = 'top_2'
    vols = load_layer(2)
    vol_fixed = vols[1]
    vol_moving = np.ascontiguousarray(vols[0][:, ::-1, ::-1])
    A_hom = get_transform(step_name, vol_fixed, vol_moving)
    vol_stitched = stitch(vol_fixed, vol_moving, A_hom)
    save_transform(A_hom, step_name)
    save_stitch(vol_stitched, step_name)

def step_43():
    step_name = 'top_43'
    vol_fixed = load_stitch('top_4')
    vol_moving = load_stitch('top_3')
    A_hom = get_transform(step_name, vol_fixed, vol_moving)
    print('Estimated transform')
    vol_stitched = stitch(vol_fixed, vol_moving, A_hom)
    print('Stitched')
    del vol_fixed, vol_moving
    save_transform(A_hom, step_name)
    save_stitch(vol_stitched, step_name)
    print('Saved stitch')

def step_21():
    step_name = 'top_21'
    vol_fixed = load_stitch('top_2')
    vol_moving = np.ascontiguousarray(load_layer(1)[0][::-1,:,::-1])

    mask_fixed = np.zeros(vol_fixed.shape, dtype=bool)
    mask_fixed[int(0.8*vol_fixed.shape[0]):,:,:] = 1
    mask_moving = np.zeros(vol_moving.shape, dtype=bool)
    mask_moving[:int(0.2*vol_moving.shape[0]),:,:] = 1

    A_hom = get_transform(step_name, vol_fixed*mask_fixed, vol_moving*mask_moving, type_of_transform='Similarity')
    print('Estimated transform')
    del mask_fixed, mask_moving
    vol_stitched = stitch(vol_fixed, vol_moving, A_hom)
    print('Stitched')
    del vol_fixed, vol_moving
    save_transform(A_hom, step_name)
    save_stitch(vol_stitched, step_name)
    print('Saved stitch')

def step_4321():
    step_name = 'top_4321'
    vol_fixed = load_stitch('top_43')
    vol_moving = load_stitch('top_21')

    mask_fixed = np.zeros(vol_fixed.shape, dtype=bool)
    mask_fixed[int(0.77*vol_fixed.shape[0]):,:,:] = 1
    mask_moving = np.zeros(vol_moving.shape, dtype=bool)
    mask_moving[:int(0.16*vol_moving.shape[0]),:,:] = 1

    A_hom = get_transform(step_name, vol_fixed*mask_fixed, vol_moving*mask_moving, type_of_transform='Similarity')
    print('Estimated transform')
    del mask_fixed, mask_moving
    vol_stitched = stitch(vol_fixed, vol_moving, A_hom)
    print('Stitched')
    del vol_fixed, vol_moving
    save_transform(A_hom, step_name)
    save_stitch(vol_stitched, step_name)
    print('Saved stitch')



STEPS = {
    'step_4_10': step_4_10,
    'step_4_23': step_4_23,
    'step_4': step_4,
    'step_3_10': step_3_10,
    'step_3_23': step_3_23,
    'step_3': step_3,
    'step_2': step_2,
    'step_43': step_43,
    'step_21': step_21,
    'step_4321': step_4321,
}

def main():
    if len(sys.argv) != 2:
        print("Usage: python stitch_pipeline.py <step_name>")
        print("Available steps:")
        for name in sorted(STEPS):
            print(" ", name)
        raise SystemExit(1)
    
    step_name = sys.argv[1]

    try:
        fn = STEPS[step_name]
    except KeyError:
        print(f"Unknown step: {step_name!r}")
        print("Available steps:")
        for name in sorted(STEPS):
            print("  ", name)
        raise SystemExit(1)

    print(f"[RUN] {step_name}")
    t0 = time.perf_counter()

    fn()

    dt = time.perf_counter() - t0
    print(f"[DONE] {step_name} in {dt:.1f} s")



if __name__ == '__main__':
    main()