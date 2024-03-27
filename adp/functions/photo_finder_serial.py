# print(f"{__name__}")

# Python modules
import os
import hashlib

# External Packages
import numpy as np
from adp.functions.dataklasses import dataklass
from PIL import Image, ImageFile, UnidentifiedImageError
ImageFile.LOAD_TRUNCATED_IMAGES = True

__all__ = ["RasterImage", "rscandir_images", "tuple_rscandir_images"]
__version__ = '0.1'
__author__ = 'Chia Yan Hon, Julian.'
__copyright__ = "Copyright 2023, Chia Yan Hon, Julian."
__license__ = "Apache License, Version 2.0"


@dataklass
class RasterImage:
    hashhex: str
    path: str
    size: int


def rscandir_images(path):
    """Recursively scan a directory (& its sub-directories) for raster images
    that PIL can open and that are unhidden. Yields the path corresponding to
    these images in str format."""

    for itr in os.scandir(path):
        if itr.is_file() and not itr.name.startswith('.'):
            try:
                im = Image.open(itr.path)
            except UnidentifiedImageError:
                pass
            except OSError:
                pass
            except ValueError:
                pass
            else:
                image = np.array(im)
                im.close()
                hashhex = hashlib.sha3_256(image).hexdigest()
                yield RasterImage(hashhex, itr.path, os.stat(itr).st_size)
        if itr.is_dir() and not itr.name.startswith('.'):
            yield from rscandir_images(itr.path)


def tuple_rscandir_images(path):
    # print(f"def tuple_rscandir_images(path):")
    rimages = tuple(rscandir_images(path))
    # print(f'{len(rimages)=} {rimages=}')
    return rimages


if __name__ == '__main__':
    from time import perf_counter
    from adp.widgets.constants import CWD

    print(f"{CWD.parent=}")
    # fpath = str(CWD.parent) + "/Samples/Photos1"
    fpath = str(CWD.parent) + "/Samples/Photos2"
    # fpath = str(CWD.parent) + "/Samples/Photos3"
    # fpath = str(CWD.parent) + "/Samples/Photos4"

    print(f'\nSerial scanning for photos started...')
    start = perf_counter()
    rsimages = tuple_rscandir_images(fpath)
    end = perf_counter()
    print(f'Serial scanning for photos completed.')
    print(f'Found {len(rsimages)} raster images in {end - start} secs.')
