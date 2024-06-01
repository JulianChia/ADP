# Python module
import queue
import threading
from itertools import combinations
from time import perf_counter

# Package modules
from adp.functions.tools import percent_complete

__all__ = ["detect_duplicates_serially"]
__version__ = '0.1.1'
__license__ = "Apache License, Version 2.0"
__copyright__ = "Copyright 2024, Chia Yan Hon, Julian."
__author__ = 'Chia Yan Hon, Julian.'
__email__ = "julianchiayh@gmail.com"


def detect_duplicates_serially(rimages: list, job_queue: queue.Queue,
							   exit_event: threading.Event = None,) -> None:
	"""Function to detect duplicated raster images by comparing their hash
	(i.e. sha3_256) hex values. Returns a dictionary of
	duplicates = {
	a_shortest_path: [longer_path1, longer_path2, ...],
	b_shortest_path: [longer_path1, longer_path2, ...],
	... }."""
	start = perf_counter()
	njobs = len(rimages)
	duplicates = dict()
	for ri in combinations(rimages, 2):
		# print(f'{ri=}')
		hash0 = ri[0].hashhex
		hash1 = ri[1].hashhex
		path0 = ri[0].path
		path1 = ri[1].path

		if hash0 in hash1:
			if hash0 == hash1:  # Same hashhex, i.e. duplicates
				if hash0 in duplicates:  # hash0 already in duplicates
					duplicates[hash0].add(path0)
					duplicates[hash0].add(path1)
				else:  # path0 not in duplicates
					duplicates[hash0] = {path0, path1}

		if isinstance(exit_event, threading.Event):
			if exit_event.is_set():
				print(f"{exit_event.is_set()=}")
				break

	percent_complete(njobs, njobs, bar_width=50, title="Duplicates",
					 print_perc=True)
	end = perf_counter()
	job_queue.put(("DupCompleted", duplicates, start, end))
