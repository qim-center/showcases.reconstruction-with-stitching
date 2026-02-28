import numpy as np
from itertools import product
import scipy.ndimage as ndi
import ants

from src.utils import profile

@profile
def estimate_transform(vol_fixed, vol_moving, **kwargs):
    # couldnt get masking to work in ants.registration, so masks needs to be multiplied on the input volumes beforehand
    # type_of_transform in ['Rigid', 'Similarity', ...]
    # aff_metric in ['mattes', 'meansquares', ...]
    # modify aff_iterations or aff_shrink_factors to speed up the process?
    kwargs.setdefault('type_of_transform', 'Rigid')

    fixed = ants.from_numpy(vol_fixed)
    moving = ants.from_numpy(vol_moving)
    reg = ants.registration(fixed, moving, **kwargs)

    tx = ants.read_transform([x for x in reg['fwdtransforms'] if x.endswith('.mat')][0])

    A = tx.parameters[:9].reshape((3, 3))
    t = tx.parameters[9:]
    c = tx.fixed_parameters

    ### Convert rigid transform from rotation-center form to standard form
    # y = A(x−c)+c+t
    # y = Ax - Ac + c + t
    A_hom = np.zeros((4, 4))
    A_hom[3, 3] = 1
    A_hom[:3, :3] = A
    A_hom[:3, 3] = -A@c + c + t

    return A_hom

@profile
def _feather_blend(vol1, vol2, mask1, mask2, eps=1e-7):
    m1 = mask1
    m2 = mask2

    d1 = ndi.distance_transform_edt(m1).astype(np.float32)
    d2 = ndi.distance_transform_edt(m2).astype(np.float32)

    # denom in d1: d1 = d1 + d2 + eps
    d1 += d2
    d1 += eps

    # d2 = w2 = d2 / denom   (in-place)
    np.divide(d2, d1, out=d2)
    del d1

    out = np.zeros_like(vol1, dtype=np.float32)

    only1 = m1 & ~m2
    out[only1] = vol1[only1]
    del only1

    only2 = m2 & ~m1
    out[only2] = vol2[only2]
    del only2

    both = m1 & m2
    out[both] = (1-d2[both]) * vol1[both] + d2[both] * vol2[both]

    return out

@profile
def stitch(vol1, vol2, A_hom, debug=False):
    shape1 = vol1.shape
    shape2 = vol2.shape

    corners1, corners2 = (
        np.array(list(product(*[(0, n) for n in v.shape])))
        for v in (vol1, vol2)
    )

    # ants gives the mapping from vol1 to vol2, but we want to go from vol2 to vol1
    A_hom = np.linalg.inv(A_hom)
    A = A_hom[:3, :3]
    t = A_hom[:3, 3]
    corners2_t = corners2 @ A.T + t

    all_corners = np.vstack((corners1, corners2_t))
    min_coords = np.floor(all_corners.min(axis=0))
    max_coords = np.ceil(all_corners.max(axis=0))

    out_shape = (max_coords - min_coords).astype(int)
    offset = np.maximum(0, (-min_coords).astype(int))

    A_hom_canvas = A_hom.copy()
    A_hom_canvas[:3, 3] += offset

    vol1_canvas = np.zeros(out_shape, dtype=np.float32)
    mask1 = np.zeros(out_shape, dtype=bool)

    slices = tuple(slice(o, o + n) for o, n in zip(offset, vol1.shape))
    vol1_canvas[slices] = vol1
    mask1[slices] = True

    # have to invert again here since scipy does a backward transform
    vol2_canvas = ndi.affine_transform(vol2, np.linalg.inv(A_hom_canvas), output_shape=out_shape, output=np.float32)
    mask2 = ndi.affine_transform(np.ones(shape2, dtype=np.uint8), np.linalg.inv(A_hom_canvas), output_shape=out_shape) > 0.5

    blended = _feather_blend(vol1_canvas, vol2_canvas, mask1, mask2)
    if debug:
        return blended, vol1_canvas, vol2_canvas
    else:
        return blended