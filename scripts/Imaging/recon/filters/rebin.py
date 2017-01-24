from __future__ import (absolute_import, division, print_function)
from recon.helper import Helper


def execute(data, rebin, mode, cores=1, chunksize=None, h=None):
    h = Helper.empty_init() if h is None else h
    h.check_data_stack(data)

    if rebin and 0 < rebin:
        if not h.multiprocessing_available():
            data = _execute_par(data, rebin, mode, cores, chunksize, h)
        else:
            data = _execute_seq(data, rebin, mode, h)
    else:
        h.tomo_print_note("Not applying any rebinning.")

    h.check_data_stack(data)
    return data


def _execute_par(data, rebin, mode, cores=1, chunksize=None, h=None):
    import scipy.misc

    resized_data = _create_reshaped_array(data.shape, rebin)

    from functools import partial
    f = partial(scipy.misc.imresize, size=rebin, interp=mode)

    resized_data = Helper.execute_async(
        data, f, cores, chunksize, "Rebinning", h, output_data=resized_data)

    h.pstop("Finished PARALLEL image resizing. New shape: {0}".format(
        resized_data.shape))

    return resized_data


def _execute_seq(data, rebin, mode, h=None):
    import scipy.misc

    resized_data = _create_reshaped_array(data.shape, rebin)

    h.prog_init(num_images, "Rebinning images")
    for idx in range(num_images):
        resized_data[idx] = scipy.misc.imresize(
            data[idx], rebin, interp=mode)

        h.prog_update(1)

    h.prog_close()

    h.pstop("Finished image resizing. New shape: {0}".format(
        resized_data.shape))

    return resized_data


def _create_reshaped_array(old_shape, rebin):
    import numpy as np
    num_images = old_shape[0]

    # use SciPy's calculation to find the expected dimensions
    # int to avoid visible deprecation warning
    expected_dimy = int(rebin * old_shape[1])
    expected_dimx = int(rebin * old_shape[2])

    h.pstart("Starting image resizing to rebin {0} with interpolation mode {1}".format(
        rebin, mode))

    # allocate memory for images with new dimensions
    return np.zeros((num_images, expected_dimy,
                     expected_dimx), dtype=np.float32)


def _execute_custom(data, config):
    """
    Downscale to for example shrink 1Kx1K images to 512x512

    @param data_vol :: 3d volume to downscale
    @param block_size :: make block_size X block_size blocks to downscale
    @param method :: either 'average' (default) or 'sum' to calculate average or sum of blocks

    Returns :: downscaled volume, with the dimensions implied by block_size, and the
    same data type as the input data volume.
    """

    if 0 != np.mod(data_vol.shape[1], block_size) or 0 != np.mod(
            data_vol.shape[2], block_size):
        raise ValueError(
            "The block size ({0}) must be an exact integer divisor of the sizes of the "
            "x and y dimensions ({1} and {2} of the input data volume".format(
                data_vol.shape[2], data_vol.shape[1], block_size))

    supported_methods = ['average', 'sum']
    if method.lower() not in supported_methods:
        raise ValueError(
            "The method to combine pixels in blocks must be one of {0}. Got unknown "
            "value: {1}".format(supported_methods, method))

    rescaled_vol = np.zeros(
        (data_vol.shape[0], data_vol.shape[1] // block_size,
         data_vol.shape[2] // block_size),
        dtype=data_vol.dtype)
    # for block averages in every slice/image along the vertical/z axis
    tmp_shape = rescaled_vol.shape[1], block_size, rescaled_vol.shape[
        2], block_size
    for vert_slice in range(len(rescaled_vol)):
        vsl = data_vol[vert_slice, :, :]
        if 'average' == method:
            rescaled_vol[vert_slice, :, :] = vsl.reshape(tmp_shape).mean(
                -1).mean(1)
        elif 'sum' == method:
            rescaled_vol[vert_slice, :, :] = vsl.reshape(tmp_shape).mean(
                -1).mean(1)

    return rescaled_vol
