# Python modules
from pathlib import Path
from typing import Union


__all__ = ["filesize", "timings", "sort_pictures_by_creation_time",
           "percent_complete", "pop_kwargs"]
__version__ = '0.1.1'
__license__ = "Apache License, Version 2.0"
__copyright__ = "Copyright 2024, Chia Yan Hon, Julian."
__author__ = 'Chia Yan Hon, Julian.'
__email__ = "julianchiayh@gmail.com"


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


def sort_pictures_by_creation_time(filestrpaths: list) -> list:
    """Identify which picture is the original and which are copies using
    their creation date. Oldest is treated as original. They are then
    sorted in ascending order, i.e. oldest first, followed by
    next younger, etc...

    Note: dps_ctime = {i.stat().st_ctime: i for i in dps}
          This dict() comprehension is too simplistic, hence it has been
          commented out and replaced with a longer for-loop check mechanism.
          Duplicated pictures can have the same creation time thereby overwriting
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


def percent_complete(step, total_steps, bar_width=60, title="",
                     print_perc=True):
    """https://stackoverflow.com/a/70586588/5722359"""
    import sys

    # UTF-8 left blocks: 1, 1/8, 1/4, 3/8, 1/2, 5/8, 3/4, 7/8
    utf_8s = ["█", "▏", "▎", "▍", "▌", "▋", "▊", "█"]
    perc = 100 * float(step) / float(total_steps)
    max_ticks = bar_width * 8
    num_ticks = int(round(perc / 100 * max_ticks))
    full_ticks = num_ticks / 8  # Number of full blocks
    part_ticks = num_ticks % 8  # Size of partial block (array index)

    disp = bar = ""  # Blank out variables
    bar += utf_8s[0] * int(full_ticks)  # Add full blocks into Progress Bar

    # If part_ticks is zero, then no partial block, else append part char
    if part_ticks > 0:
        bar += utf_8s[part_ticks]

    # Pad Progress Bar with fill character
    bar += "▒" * int((max_ticks / 8 - float(num_ticks) / 8.0))

    if len(title) > 0:
        disp = title + ": "  # Optional title to progress display

    # Print progress bar in green: https://stackoverflow.com/a/21786287/6929343
    disp += "\x1b[0;32m"  # Color Green
    disp += bar  # Progress bar to progress display
    disp += "\x1b[0m"  # Color Reset
    if print_perc:
        # If requested, append percentage complete to progress display
        if perc > 100.0:
            perc = 100.0  # Fix "100.04 %" rounding error
        disp += " {:6.2f}".format(perc) + " %"

    # Output to terminal repetitively over the same line using '\r'.
    sys.stdout.write("\r" + disp)
    sys.stdout.flush()


def pop_kwargs(key: str, possiblevalues: Union[list, tuple], kwargs: dict) ->\
        Union[str, int, float]:
    """Function to pop options. For `possiblevalues`, its first value must
    be the default value of `key`."""
    try:
        value = kwargs.pop(key)
    except KeyError:
        return possiblevalues[0]  # default to first possible values
    else:
        if value in possiblevalues:
            return value
        else:
            raise ValueError(f"{key}={value} is invalid. It's value must be"
                             f"one of these: {possiblevalues}.")