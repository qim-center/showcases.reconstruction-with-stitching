from src.utils import profile, timed
from src.io import load_layer, load_transform
from src.volume_stitcher import estimate_transform, stitch

@profile
def step_4_23():
    step_name = 'top_4_23'
    vol_fixed, vol_moving = load_layer(4, (2, 3))
    with timed('estimate_transform'):
        A_hom = estimate_transform(vol_fixed, vol_moving)
    with timed('stitch'):
        vol_stitched = stitch(vol_fixed, vol_moving, A_hom)

@profile
def step_4_23_est():
    print('Only estimation')
    step_name = 'top_4_23'
    vol_fixed, vol_moving = load_layer(4, (2, 3))
    A_hom = estimate_transform(vol_fixed, vol_moving)

@profile
def step_4_23_stitch():
    print('Only stitching')
    step_name = 'top_4_23'
    vol_fixed, vol_moving = load_layer(4, (2, 3))
    A_hom = load_transform(step_name)
    vol_stitched = stitch(vol_fixed, vol_moving, A_hom)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        raise ValueError("Provide function name as argument")

    func_name = sys.argv[1]

    if func_name not in globals():
        raise ValueError(f"Function '{func_name}' not found")

    func = globals()[func_name]

    if not callable(func):
        raise ValueError(f"'{func_name}' is not callable")

    func()