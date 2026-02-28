import os

from cil.io import NikonDataReader
# TIGRE is faster on large-scale CT according to https://tomopedia.github.io/software/tigre/
from cil.recon import FDK # Uses TIGRE
from cil.processors import TransmissionAbsorptionConverter, Padder

def get_pixel_nums(xtekct_path):
    """
    Get number of pixels on the detector panel.
    """
    reader = NikonDataReader(file_name=xtekct_path)
    num_pixels_h = reader.get_geometry().pixel_num_h
    num_pixels_v = reader.get_geometry().pixel_num_v
    return num_pixels_h, num_pixels_v

def reconstruct_with_padding(data, pad_factor, size='original'):
    """
    data: AcquisitionData object representing the sinogram
    pad_factor: The percentage that should be padded horizontally on each edge.
                Heuristic to choose at least 0.25 or larger; otherwise the circle artifact may still reside.
    size: 'original' if the reconstruction should be the same size as the original ImageGeometry
          'padded' to get the correspondingly padded reconstruction. Used to see the circle artifact.
    """
    dim_horizontal = data.get_data_axes_order().index('horizontal')
    pad_width = round(pad_factor * data.shape[dim_horizontal])
    data_padded = Padder.edge(pad_width={'horizontal': pad_width})(data)
    data_padded.reorder(order='tigre')
    if size == 'original':
        ig = data.geometry.get_ImageGeometry()
        return FDK(data_padded, ig).run(verbose=0)
    elif size == 'padded':
        return FDK(data_padded).run(verbose=0)
    else:
        raise ValueError

def reconstruct(data):
    data.reorder(order='tigre')
    return FDK(data).run(verbose=0)

def read_and_process(file_name, center_height='full'):
    if not os.path.isfile(file_name):
        raise ValueError
    
    num_pixels_h, num_pixels_v = get_pixel_nums(file_name)
    if center_height == 'full':
        reader = NikonDataReader(file_name=file_name)
    else:
        center_height = int(center_height)
        slice_dict = {'vertical': (
            num_pixels_v // 2 - center_height // 2,
            num_pixels_v // 2 + center_height // 2,
            1
        )}
        reader = NikonDataReader(file_name=file_name, roi=slice_dict)
    
    data = reader.read()
    return TransmissionAbsorptionConverter()(data)