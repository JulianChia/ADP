# Python modules
import os
import hashlib
import queue
import threading
import math
import concurrent.futures as cf
from typing import Union, Generator
from time import perf_counter

# Package module
from adp.functions.tools import percent_complete

# External Packages
import numpy as np
from adp.functions.dataklasses import dataklass
from PIL import Image, ImageFile, UnidentifiedImageError
ImageFile.LOAD_TRUNCATED_IMAGES = True

__all__ = ["RasterImage", "get_filepaths_in", "get_image",
           "get_rasterimages_in_one_folder_concurrently"]
__version__ = '0.1.1'
__license__ = "Apache License, Version 2.0"
__copyright__ = "Copyright 2024, Chia Yan Hon, Julian."
__author__ = 'Chia Yan Hon, Julian.'
__email__ = "julianchiayh@gmail.com"


@dataklass
class RasterImage:
    hashhex: str
    path: str
    size: int


def get_filepaths_in(folder: Union[str, bytes, os.PathLike],) -> Generator:
    for itr in os.scandir(folder):
        if itr.is_file() and not itr.name.startswith('.'):
            yield itr.path


def get_image(filepath: Union[str, bytes, os.PathLike]) -> RasterImage:
    try:
        im = Image.open(filepath)
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
            return RasterImage(hashhex, filepath, os.stat(filepath).st_size)


def get_rasterimages_in_one_folder_concurrently(
        folder: Union[str, bytes, os.PathLike],
        job_queue: queue.Queue,
        ncpu: int = os.cpu_count(),
        cfe: str = "Process",
        exit_event: threading.Event = None,) -> None:
    """Function to detect pictures in 'folders' concurrently. Its progress and
       results can be extracted from 'job_queue'. Progress is also printed to
       the terminal."""
    start = perf_counter()

    filepaths = tuple(get_filepaths_in(folder))
    njobs = len(filepaths)
    jobs_completed = 0
    pbformat = {"bar_width": 50, "title": "Pictures  ", "print_perc": True}
    percent_complete(jobs_completed, njobs, **pbformat)

    rasterimages = []
    chunksize = 1  # Optimised
    match cfe:
        case "process": executor = cf.ProcessPoolExecutor(max_workers=ncpu)
        case "thread": executor = cf.ThreadPoolExecutor(max_workers=ncpu)
    with executor as execu:
        results = execu.map(get_image, filepaths,
                            chunksize=chunksize, timeout=60*10)
        for result in results:
            # Emergency exit
            if isinstance(exit_event, threading.Event):
                if exit_event.is_set():
                    break
            # Get results
            if result:
                rasterimages.append(result)
            # Update progress in terminal and queue
            jobs_completed += 1
            percent_complete(jobs_completed, njobs, **pbformat)
            job_queue.put(("FindRunning", jobs_completed, njobs))
    # Inform queue that job has completed
    end = perf_counter()
    job_queue.put(("FindCompleted", rasterimages, start, end))
