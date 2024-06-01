# Python modules
import os
import hashlib
import concurrent.futures as cf
import queue
import threading
import math
from datetime import datetime
from typing import Union, Generator
from time import perf_counter

# Package module
from adp.functions.dataklasses import dataklass
from adp.functions.tools import percent_complete

# External Packages
import numpy as np
from PIL import Image, ImageFile, UnidentifiedImageError
ImageFile.LOAD_TRUNCATED_IMAGES = True
# PIL.Hdf5StubImagePlugin.register_handler()


__all__ = ["RasterImage", "scandir_images_concurrently", "fast_scandir",
           "scandir_images", "list_scandir_images"]
__version__ = '0.1.1'
__license__ = "Apache License, Version 2.0"
__copyright__ = "Copyright 2024, Chia Yan Hon, Julian."
__author__ = 'Chia Yan Hon, Julian.'
__email__ = "julianchiayh@gmail.com"


@dataklass
class RasterImage:
    """A dataklass to store the hashhex, path and size of a raster image."""
    hashhex: str
    path: str
    size: int


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


def scandir_images(dirpath: Union[str, bytes, os.PathLike]) -> Generator[
    RasterImage, None, None]:
    """Function to scan a directory for unhidden raster images that PIL can
    open. Yields RasterImages instance of these image files."""
    # print(f"scandir_images {threading.main_thread()=}"
    #       f" {threading.current_thread()=}")
    # print(f"               {threading.active_count()=}"
    #       f" {threading.enumerate()=}")
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
                except OSError as exc1:
                    # print(f"  Skipped {itr.path}: {exc1}")
                    pass
                except SyntaxError as exc2:
                    # print(f"  Skipped {itr.path}: {exc2}")
                    pass
                else:
                    img = np.asarray(im)
                    im.close()
                    hashhex = hashlib.sha3_256(img).hexdigest()
                    del img
                    yield RasterImage(hashhex, itr.path, os.stat(itr).st_size)


def list_scandir_images(path: Union[str, bytes, os.PathLike]) -> list:
    """Function returns a tuple of RasterImage instances found in path."""
    # print(f"{threading.main_thread()=} {threading.current_thread()=}")
    return list(scandir_images(path))


def scandir_images_concurrently(folders: list,
                                job_queue: queue.Queue,
                                ncpu : int = os.cpu_count(),
                                cfe: str = "Process",
                                exit_event: threading.Event = None,) -> None:
    """Function to detect pictures in 'folders' concurrently. Its progress and
    results can be extracted from 'job_queue'. Progress is also printed to
    the terminal."""
    start = perf_counter()

    njobs = len(folders)
    jobs_completed = 0
    pbformat = {"bar_width": 50, "title": "Pictures  ", "print_perc": True}
    percent_complete(jobs_completed, njobs, **pbformat)

    rasterimages = []
    chunksize = 1  # Optimised
    match cfe:
        case "process": executor = cf.ProcessPoolExecutor(max_workers=ncpu)
        case "thread": executor = cf.ThreadPoolExecutor(max_workers=ncpu)
    with executor as execu:
        results = execu.map(list_scandir_images, folders,
                            chunksize=chunksize, timeout=60*10)
        for result in results:
            # Emergency exit
            if isinstance(exit_event, threading.Event):
                if exit_event.is_set():
                    break
            # Get results
            if result:
                rasterimages.extend(result)
            # Update progress in terminal and queue
            jobs_completed += 1
            percent_complete(jobs_completed, njobs, **pbformat)
            job_queue.put(("FindRunning", jobs_completed, njobs))
    # Inform queue that job has completed
    end = perf_counter()
    job_queue.put(("FindCompleted", rasterimages, start, end))

