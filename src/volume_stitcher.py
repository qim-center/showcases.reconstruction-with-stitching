import numpy as np
from itertools import product
import scipy.ndimage as ndi
import ants
from collections.abc import Sequence

from src.utils import profile, monitor

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

def _bbox_from_mask(mask: np.ndarray) -> tuple[slice, ...]:
    """
    Return the tight bounding box of a non-empty boolean mask as a tuple of slices.

    Parameters
    ----------
    mask
        An N-dimensional boolean array. Must contain at least one True value.

    Returns
    -------
    tuple[slice, ...]
        One slice per dimension, suitable for `mask[bbox]`.

    Raises
    ------
    TypeError
        If `mask` is not of boolean dtype.
    ValueError
        If `mask` contains no True values.
    """
    if mask.dtype != np.bool_:
        raise TypeError(f"Expected boolean mask, got {mask.dtype}")

    if not mask.any():
        raise ValueError("bbox_from_mask() received an empty mask")

    axes = range(mask.ndim)

    bbox = []
    for ax in axes:
        other_axes = tuple(i for i in axes if i != ax)
        occupied = mask.any(axis=other_axes)

        start = occupied.argmax()
        stop = occupied.size - occupied[::-1].argmax()

        bbox.append(slice(start, stop))

    return tuple(bbox)

def _expand_slices(
    slices: tuple[slice, ...],
    margin: int | Sequence[int],
    shape: tuple[int, ...] | None = None,
) -> tuple[slice, ...]:
    """
    Expand each slice by `margin` on both sides.

    Parameters
    ----------
    slices
        Tuple of slice objects.
    margin
        Either a scalar (applied to all axes) or per-axis sequence.
    shape
        Optional array shape. If provided, results are clipped to [0, dim].

    Returns
    -------
    tuple[slice, ...]
        Expanded slices.
    """
    if isinstance(margin, int):
        margins = (margin,) * len(slices)
    else:
        if len(margin) != len(slices):
            raise ValueError("margin must match number of dimensions")
        margins = tuple(margin)

    expanded = []

    for i, (slc, m) in enumerate(zip(slices, margins)):
        if slc.step not in (None, 1):
            raise ValueError("expand_slices only supports step=None or 1")

        start = slc.start - m
        stop = slc.stop + m

        if shape is not None:
            start = max(start, 0)
            stop = min(stop, shape[i])

        expanded.append(slice(start, stop))

    return tuple(expanded)

@profile
def _feather_blend(vol1, vol2, mask1, mask2, approximate=False, eps=1e-7):
    """
    approximate:
        If True, uses distance_transform_cdt. If False, uses distance_transform_edt.
        distance_transform_cdt is less precise but faster and uses less memory than distance_transform_edt
    """
    def distance_transform_cdt(m):
        # distance_transform_cdt only accepts int32
        d = np.empty(m.shape, dtype=np.int32)
        ndi.distance_transform_cdt(m, metric='chessboard', return_distances=True, distances=d)
        d = d.astype(np.float32)
        return d

    def distance_transform_edt(m):
        # distance_transform_edt only accepts float64
        d = np.empty(m.shape, dtype=np.float64)
        ndi.distance_transform_edt(m, return_distances=True, distances=d)
        d = d.astype(np.float32)
        return d
    
    distance_transform = distance_transform_cdt if approximate else distance_transform_edt
    
    m1 = mask1
    m2 = mask2

    both = m1 & m2
    bb = _bbox_from_mask(both)
    bb_padded = _expand_slices(bb, margin=1, shape=both.shape)

    with monitor('distance_transform'):
        d1 = distance_transform(m1[bb_padded])[1:-1, 1:-1, 1:-1]
        d2 = distance_transform(m2[bb_padded])[1:-1, 1:-1, 1:-1]

    denom = d1 # d1 is unused from now on
    np.add(denom, d2 + eps, out=denom)

    w2 = d2 # d2 is unused from now on
    np.divide(w2, denom, out=w2)

    out = vol1.copy()

    only2 = m2 & ~m1
    out[only2] = vol2[only2]

    both_sub = both[bb]
    out_sub = out[bb]
    v1_sub = vol1[bb]
    v2_sub = vol2[bb]

    out_sub[both_sub] = (1 - w2[both_sub]) * v1_sub[both_sub] + w2[both_sub] * v2_sub[both_sub]

    return out

@profile
def stitch(vol1, vol2, A_hom, approximate=False, debug=False):
    """
    approximate:
        much faster and much lower memory traded off for slightly lower accuracy (may not be noticeable)
    debug:
        returns the two temporary individual volume canvases, useful for debugging or visualization purposes
    """
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

    with monitor(f'affine_transform (approximate={approximate})'):
        # have to invert transform again here since scipy does a backward transform
        if approximate:
            # from the documentation of affine_transform:
            # """
            # prefilter:
            # ... The default is True, which will create a temporary float64 array ...
            # ... If setting this to False, the output will be slightly blurred if order > 1 ...
            # """
            # so to avoid this extra memory and to make it faster, we set prefilter=False and order=1 to avoid the blurriness
            vol2_canvas = ndi.affine_transform(vol2, np.linalg.inv(A_hom_canvas), output_shape=out_shape, output=np.float32, prefilter=False, order=1)
            mask2 = ndi.affine_transform(np.ones(shape2, dtype=np.uint8), np.linalg.inv(A_hom_canvas), output_shape=out_shape, prefilter=False, order=1) > 0.5
        else:
            vol2_canvas = ndi.affine_transform(vol2, np.linalg.inv(A_hom_canvas), output_shape=out_shape, output=np.float32)
            mask2 = ndi.affine_transform(np.ones(shape2, dtype=np.uint8), np.linalg.inv(A_hom_canvas), output_shape=out_shape) > 0.5
    
    # do vol2_canvas and mask2 first since those create temporary memory, requiring higher peak memory
    vol1_canvas = np.zeros(out_shape, dtype=np.float32)
    mask1 = np.zeros(out_shape, dtype=bool)

    slices = tuple(slice(o, o + n) for o, n in zip(offset, vol1.shape))
    vol1_canvas[slices] = vol1
    mask1[slices] = True

    with monitor(f'_feather_blend (approximate={approximate})'):
        blended = _feather_blend(vol1_canvas, vol2_canvas, mask1, mask2, approximate=approximate)
    
    if debug:
        return blended, vol1_canvas, vol2_canvas
    else:
        return blended