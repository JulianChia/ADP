# print(f"{__name__}")

# Python modules
import os
import concurrent.futures as cf

__all__ = ["detect_duplicates_concurrently"]
__version__ = '0.1'
__author__ = 'Chia Yan Hon, Julian.'
__copyright__ = "Copyright 2023, Chia Yan Hon, Julian."
__license__ = "Apache License, Version 2.0"


def reshape_tuple1d(tuple1d, n):
    """Function to reshape a 1D tuple into a 2D list with n number of
    sub-lists of elements."""

    if len(tuple1d) < n:
        raise ValueError(
            'Size of tuple1d needs to be greater than or equal to n.')

    sub_list_size = len(tuple1d) // n
    remainder = len(tuple1d) % n
    new_list = []

    # How to handle elements of tuple1d that is divisible by n.
    for i in range(0, len(tuple1d) - remainder, sub_list_size):
        new_list.append(list(tuple1d[i: i + sub_list_size]))
    # Insert each remainder elements into each sub_list of new_list.
    if remainder > 0:
        for en, m in enumerate(tuple1d[-remainder:]):
            new_list[en].extend([m])

    return new_list


def check_hash_duplication(batch, rasterimages):
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


def detect_duplicates_concurrently(rasterimages,
                                   ncpu : int = os.cpu_count(),
                                   cfe: str = "thread"):
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

    batches = reshape_tuple1d(rasterimages, ncpu)
    futures = []
    print(f'Concurrent {cfe} scanning for duplicates has started...')
    with executor(max_workers=ncpu) as execu:
        for batch in batches:
            futures.append(
                execu.submit(check_hash_duplication, batch, rasterimages)
            )

    duplicates = dict()
    for f in cf.as_completed(futures):
        results = f.result()  # dict returned by each future
        if any(results):
            for k, v in results.items():  # each element of dict
                if k not in duplicates:
                    duplicates[k] = v
                else:
                    duplicates[k].union(v)
    # print(f'concurrent - {len(duplicates)=} {duplicates=}')

    print(f'Concurrent {cfe} scanning for duplicates has completed.')
    return duplicates


if __name__ == '__main__':
    # Python module
    from time import perf_counter

    # Project modules
    import photo_finder_concurrent as pfc
    import duplicates_finder_serial as dfs
    from adp.widgets.constants import CWD

    print(f"{CWD.parent=}")
    # fpath = str(CWD.parent) + "/Samples/Photos1"
    # fpath = str(CWD.parent) + "/Samples/Photos2"
    # fpath = str(CWD.parent) + "/Samples/Photos3"
    fpath = str(CWD.parent) + "/Samples/Photos4"
    # fpath = str(Path().home())

    start0 = perf_counter()
    subdirs = pfc.fast_scandir(fpath)
    end0 = perf_counter()
    print(f"\nFound {len(tuple(subdirs))} sub-dirs in {end0 - start0} secs.")

    print()
    start1 = perf_counter()
    photos = pfc.scandir_images_concurrently([fpath] + subdirs, cfe="process")
    end1 = perf_counter()
    method1 = end1 - start1
    print(f"Found {len(photos)} raster image in {method1} secs.")

    print()
    start2 = perf_counter()
    cduplicates = detect_duplicates_concurrently(photos, cfe="process")
    end2 = perf_counter()
    method2 = end2 - start2
    ncdup = sum([len(i) for i in cduplicates.values()])
    print(f"Found {ncdup} duplicates in {method2} secs.")

    print(f'\nSerial scanning for duplicate photos started...')
    start3 = perf_counter()
    sduplicates = dfs.detect_duplicates_serially(photos)
    end3 = perf_counter()
    print(f'Serial scanning for duplicate photos completed.')
    method3 = end3 - start3
    nsdup = sum( [len(i) for i in sduplicates.values()] )
    print(f"Found {nsdup} duplicates in {method3} secs.")

    print(f"\nConcurrent is {method2 / method3} times of Serial.")

