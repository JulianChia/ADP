# Python modules
import queue
import threading
import os
import concurrent.futures as cf
from itertools import repeat
from time import perf_counter

# Package modules
from adp.functions.tools import percent_complete

__all__ = ["detect_duplicates_concurrently", "reshape_list1d",
           "check_hash_duplication"]
__version__ = '0.1'
__license__ = "Apache License, Version 2.0"
__copyright__ = "Copyright 2024, Chia Yan Hon, Julian."
__author__ = 'Chia Yan Hon, Julian.'
__email__ = "julianchiayh@gmail.com"


def reshape_list1d(list1d: list, n: int) -> list:
    """Function to reshape a 1D list into a 2D list with n number of
    sub-lists of elements."""

    if len(list1d) < n:
        raise ValueError(
            'Size of list1d needs to be greater than or equal to n.')

    sub_list_size = len(list1d) // n
    remainder = len(list1d) % n
    new_list = []

    # How to handle elements of list1d that is divisible by n.
    for i in range(0, len(list1d) - remainder, sub_list_size):
        new_list.append(list(list1d[i: i + sub_list_size]))
    # Insert each remainder elements into each sub_list of new_list.
    if remainder > 0:
        for en, m in enumerate(list1d[-remainder:]):
            new_list[en].extend([m])

    return new_list


def check_hash_duplication(batch: list, rasterimages: list) -> dict:
    """Function to detect duplicated hash of raster images."""
    # print(f"check_hash_duplication {threading.main_thread()=}"
    #       f" {threading.current_thread()=}")
    duplicates = dict()
    checked = set()
    for bi in batch:
        hash0 = bi.hashhex
        path0 = bi.path
        checked.add(path0)

        for img in rasterimages:
            path1 = img.path
            if path1 in checked:
                pass   # Skip those with same path
            else:
                hash1 = img.hashhex
                if hash0 == hash1:  # Same hashhex, i.e. duplicates
                    if hash0 in duplicates:  # hash0 already in duplicates
                        duplicates[hash0].add(path0)
                        duplicates[hash0].add(path1)
                    else:  # path0 not in duplicates
                        duplicates[hash0] = {path0, path1}

    return duplicates


def detect_duplicates_concurrently(rasterimages: list,
                                   job_queue: queue.Queue,
                                   ncpu: int = os.cpu_count(),
                                   cfe: str = "Process",
                                   exit_event=None,) -> None:
    """Function to detect duplicates in `rasterimages` concurrently. Its
    progress and result can be extracted from `job_queue`. Progress is also
    printed to the terminal."""
    start = perf_counter()

    batches = reshape_list1d(rasterimages, ncpu)
    njobs = len(batches)
    jobs_completed = 0
    pbformat = {"bar_width": 50, "title": "Duplicates", "print_perc": True}
    percent_complete(jobs_completed, njobs, **pbformat)

    duplicates = dict()
    chunksize = 1  # Optimised
    match cfe:
        case "process": executor = cf.ProcessPoolExecutor(max_workers=ncpu)
        case "thread": executor = cf.ThreadPoolExecutor(max_workers=ncpu)
    with executor as execu:
        results = execu.map(check_hash_duplication,
                            batches, repeat(rasterimages, njobs),
                            chunksize=chunksize,
                            timeout=60*10)
        for result in results:
            # Emergency exit
            if isinstance(exit_event, threading.Event):
                if exit_event.is_set():
                    break
            # Get results
            if any(result):
                for k, v in result.items():  # each element of dict
                    if k not in duplicates:
                        duplicates[k] = v
                    else:
                        duplicates[k].union(v)
            # Update progress in terminal & queue
            jobs_completed += 1
            percent_complete(jobs_completed, njobs, **pbformat)
            job_queue.put(("DupRunning", jobs_completed, njobs))
    # Inform queue that job has completed
    end = perf_counter()
    job_queue.put(("DupCompleted", duplicates, start, end))


# def detect_duplicates_concurrently(rasterimages: list,
#                                    ncpu : int = os.cpu_count(),
#                                    cfe: str = "thread") -> dict:
#     if cfe not in ["process", "thread"]:
#         ValueError(f"cfe={cfe} is invalid. It's value must either be "
#                    f"'process' or 'thread'.")
#     else:
#         if cfe in "process":
#             # print(f"- using concurrent.future.ProcessPoolExecutor")
#             executor = cf.ProcessPoolExecutor
#         else:
#             # print(f"- using concurrent.future.ThreadPoolExecutor")
#             executor = cf.ThreadPoolExecutor
#
#     batches = reshape_list1d(rasterimages, ncpu)
#     njobs = len(batches)
#     jobs_completed = 0
#
#     def _on_complete(ifuture):
#         nonlocal jobs_completed
#         # Update record on the number of completed jobs
#         jobs_completed += 1
#         percent_complete(jobs_completed, njobs, bar_width=60, title="",
#                          print_perc=True)
#
#     futures = []
#     print(f'Concurrent {cfe} scanning for duplicates has started...')
#     with executor(max_workers=ncpu) as execu:
#         for batch in batches:
#             future = execu.submit(check_hash_duplication, batch, rasterimages)
#             future.add_done_callback(_on_complete)
#             futures.append(future)
#
#     duplicates = dict()
#     for f in cf.as_completed(futures):
#         results = f.result()  # dict returned by each future
#         if any(results):
#             for k, v in results.items():  # each element of dict
#                 if k not in duplicates:
#                     duplicates[k] = v
#                 else:
#                     duplicates[k].union(v)
#     # print(f'concurrent - {len(duplicates)=} {duplicates=}')
#
#     # print(f'Concurrent {cfe} scanning for duplicates has completed.')
#     return duplicates
