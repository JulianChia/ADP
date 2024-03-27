# print(f"{__name__}")

# Python module
from itertools import combinations

__all__ = ["detect_duplicates_serially"]
__version__ = '0.1'
__author__ = 'Chia Yan Hon, Julian.'
__copyright__ = "Copyright 2023, Chia Yan Hon, Julian."
__license__ = "Apache License, Version 2.0"


def detect_duplicates_serially(rimages):
	"""Function to detect duplicated raster images by comparing their hash
	(i.e. sha3_256) hex values. Returns a dictionary of
	duplicates = {
	a_shortest_path: [longer_path1, longer_path2, ...],
	b_shortest_path: [longer_path1, longer_path2, ...],
	... }."""
	# print(f"\ndef detect_duplicates_serially(rimages):")
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

	# print(f'serial - {len(duplicates)=} {duplicates=}')
	return duplicates


if __name__ == '__main__':
	# Python module
	from time import perf_counter
	# Project module
	import photo_finder_serial as pfs
	from adp.widgets.constants import CWD

	print(f"{CWD.parent=}")
	# fpath = str(CWD.parent) + "/Samples/Photos1"
	fpath = str(CWD.parent) + "/Samples/Photos2"
	# fpath = str(CWD.parent) + "/Samples/Photos3"
	# fpath = str(CWD.parent) + "/Samples/Photos4"

	print(f'\nSerial scanning for photos started...')
	start1 = perf_counter()
	photos = pfs.tuple_rscandir_images(fpath)
	end1 = perf_counter()
	print(f'Serial scanning for photos completed.')
	print(f'Found {len(photos)} raster images in {end1 - start1} secs.')

	print(f'\nSerial scanning for duplicate photos started...')
	start2 = perf_counter()
	pduplicates = detect_duplicates_serially(photos)
	end2 = perf_counter()
	print(f'Serial scanning for duplicate photos completed.')
	ndup = sum([len(i) for i in pduplicates.values()])
	print(f'Found {ndup} duplicates in {end2 - start2} secs.')

