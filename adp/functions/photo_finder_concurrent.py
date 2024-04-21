# Python modules
import os
import hashlib
import concurrent.futures as cf
import math
from itertools import chain
from datetime import datetime
from typing import Union

# Package module
from adp.functions.dataklasses import dataklass

# External Packages
import numpy as np
from PIL import Image, ImageFile, UnidentifiedImageError
ImageFile.LOAD_TRUNCATED_IMAGES = True
# PIL.Hdf5StubImagePlugin.register_handler()


__all__ = ["RasterImage", "scandir_images", "tuple_scandir_images",
           "fast_scandir", "scandir_images_concurrently"]
__version__ = '0.1'
__author__ = 'Chia Yan Hon, Julian.'
__copyright__ = "Copyright 2023, Chia Yan Hon, Julian."
__license__ = "Apache License, Version 2.0"


def now():
    """Function returns current date and time in "dd/mm/yyyy hh:mm:ss" format.
    """
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


@dataklass
class RasterImage:
    """A dataklass to store the hashhex, path and size of a raster image."""
    hashhex: str
    path: str
    size: int


def scandir_images(dirpath: Union[str, bytes, os.PathLike]) -> RasterImage:
    """Function to scan a directory for unhidden raster images that PIL can
    open. Yields RasterImages instance of these image files."""
    # print(f"scandir_images {threading.main_thread()=}"
    #       f" {threading.current_thread()=}")
    for itr in os.scandir(dirpath):
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
                csize = im.size
                newsize = tuple(math.floor(i/10) for i in csize)
                for i in newsize:
                    if i < 60:
                        newsize = csize
                        break
                try:
                    im = im.resize(newsize,
                                   resample=Image.Resampling.NEAREST,
                                   reducing_gap=1.1)
                except OSError:
                    pass
                else:
                    img = np.asarray(im)
                    im.close()
                    hashhex = hashlib.sha3_256(img).hexdigest()
                    yield RasterImage(hashhex, itr.path, os.stat(itr).st_size)


def tuple_scandir_images(path: Union[str, bytes, os.PathLike]):
    """Function returns a tuple of RasterImage instances found in path."""
    # print(f"{threading.main_thread()=} {threading.current_thread()=}")
    rimages = tuple(scandir_images(path))
    # print(f'{len(rimages)=} {rimages=}')
    return rimages


def fast_scandir(dirname: Union[str, bytes, os.PathLike]):
    """Function to recursively find all sub-directory paths in dirname and
    return a list of all sub-directory paths (i.e. string objects)."""
    subfolders = [f.path for f in os.scandir(dirname) if f.is_dir() and not
                  f.name.startswith('.')]
    for foldername in tuple(subfolders):
        try:
            folder = fast_scandir(foldername)
        except PermissionError:
            print(f"## Skipped {foldername} due to PermissionError.")
            pass
        else:
            subfolders.extend(folder)
    return subfolders


def scandir_images_concurrently(folders: list,
                                ncpu : int = os.cpu_count(),
                                cfe: str = "thread") -> list:
    """Function to quickly return a list of RasterImage dataklass instances
    using the concurrent.futures.ProcessPoolExecutor or
    concurrent.futures.ThreadPoolExecutor subclass object. """
    if cfe not in ["process", "thread"]:
        ValueError(f"cfe={cfe} is invalid. It's value must either be "
                   f"'process' or 'thread'.")
    else:
        if cfe in "process":
            # print(f"- using concurrent.future.ProcessPoolExecutor")
            executor = cf.ProcessPoolExecutor
        else:
            # print(f"- using concurrent.future.ThreadPoolExecutor")
            executor = cf.ThreadPoolExecutor

    futures = []
    print(f'Concurrent {cfe} scanning of photos has started...')
    with executor(max_workers=ncpu) as execu:
        for folder in folders:
            futures.append(execu.submit(tuple_scandir_images, folder))
    print(f'Concurrent {cfe} scanning of photos has completed.')
    return list(chain.from_iterable(f.result() for f in cf.as_completed(
        futures)))


if __name__ == '__main__':
    from time import perf_counter
    from adp.widgets.constants import CWD

    print(f"{CWD.parent=}")
    # fpath = str(CWD.parent) + "/Samples/Photos1"
    fpath = str(CWD.parent) + "/Samples/Photos2"
    # fpath = str(CWD.parent) + "/Samples/Photos3"
    # fpath = str(CWD.parent) + "/Samples/Photos4"
    # fpath = str(Path().home())

    start0 = perf_counter()
    subdirs = fast_scandir(fpath)
    end0 = perf_counter()
    method0 = end0 - start0
    print(f"\nFound {len(tuple(subdirs))} sub-dirs in {method0} secs.")

    # Function Approach
    print(f"\ndef scandir_images_concurrently:")
    start1 = perf_counter()
    photos = scandir_images_concurrently([fpath] + subdirs, cfe="process")
    end1 = perf_counter()
    method1 = end1 - start1
    print(f"Found {len(photos)} raster image in {method1} secs.")

