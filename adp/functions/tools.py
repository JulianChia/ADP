# print(f"{__name__}")

# Python modules
from pathlib import Path

__all__ = ["filesize", "timings", "sort_photos_by_creation_time"]


def filesize(size: float) -> tuple:
    """Function to return the quantity and unit of the 'size' argument."""
    kb = 1000.0
    mb = kb * kb
    gb = mb * kb
    if size >= gb:
        return size / gb, 'GB'
    if size >= mb:
        return size / mb, 'MB'
    if size >= kb:
        return size / kb, 'KB'
    return size, 'B'


def timings(time: float) -> tuple:
    """Function to return the quantity and unit of the 'time' argument."""
    sec1 = 1.0
    min1 = 60.0 * sec1
    hr1 = 60 * min1
    day1 = 24 * hr1
    if time >= day1:
        return time/day1, 'days'
    if time >= hr1:
        return time/hr1, 'hrs'
    if time >= min1:
        return time/min1, 'mins'
    return time, 'secs'


def sort_photos_by_creation_time(filestrpaths: list) -> list:
    """Identify which photo is the original and which are copies using
    their creation date. Oldest is treated as original. They are then
    sorted in ascending order, i.e. oldest first, followed by
    next younger, etc...

    Note: dps_ctime = {i.stat().st_ctime: i for i in dps}
          This dict() comprehension is too simplistic, hence it has been
          commented out and replaced with a longer for-loop check mechanism.
          Duplicated photos can have the same creation time thereby overwriting
          the values of an existing key of a dict().
        """
    dps = tuple(Path(i) for i in sorted(filestrpaths, reverse=True))
    # dps_ctime = {i.stat().st_ctime: i for i in dps}
    dps_ctime = {}
    for p in dps:
        ctime = p.stat().st_ctime
        if ctime in dps_ctime.keys():
            dps_ctime[ctime].append(p)
        else:
            dps_ctime[ctime] = [p]
    ordered_ctime = sorted(dps_ctime.keys())
    ordered_paths = []
    for i in ordered_ctime:
        ordered_paths.extend(dps_ctime[i])
    # print(f"{dps=}")
    # print(f"{dps_ctime=}")
    # print(f"{ordered_ctime=}")
    # print(f"{ordered_paths=}")
    return ordered_paths
