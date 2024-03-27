# print(f"{__name__}")

import sqlite3
from datetime import datetime
from pathlib import Path
from itertools import count
from typing import Literal

from adp.widgets.constants import CWD, GROUPS_IN_A_PAGE
from adp.functions import sort_photos_by_creation_time, filesize

__all_ = ["DuplicatesDB"]
__version__ = '0.1'
__author__ = 'Chia Yan Hon, Julian.'
__copyright__ = "Copyright 2024, Chia Yan Hon, Julian."
__license__ = "Apache License, Version 2.0"


class DuplicatesDB:
	"""Class to create a SQLITE3 database to store photo duplicates info."""

	def __init__(self):
		self.file = CWD / "adp_db.sqlite3"
		# try:
		# 	self.file.touch(exist_ok=False)
		# except FileExistsError:
		# 	self.file.unlink()
		# 	self.file.touch()
		# 	print(f"Recreated {self.file=}")
		# else:
		# 	print(f"Created {self.file=}")
		# finally:
		# 	self.con = sqlite3.connect(self.file,
		# 							   detect_types=sqlite3.PARSE_DECLTYPES,
		# 							   # check_same_thread=False,
		# 							   )
		self.con = sqlite3.connect(":memory:",
								   detect_types=sqlite3.PARSE_DECLTYPES,
								   # check_same_thread = False,
								   )
		# self.con = sqlite3.connect("",
		# 						     detect_types=sqlite3.PARSE_DECLTYPES)
		self.con.execute('PRAGMA journal_mode = WAL')
		self.cur = self.con.cursor()
		self.create_table()

	def create_table(self):
		table = """CREATE TABLE IF NOT EXISTS
				duplicates (
					sn INTEGER,
					item_id TEXT PRIMARY KEY,
					group_id TEXT,
					hashhex TEXT,
					full_path TEXT,
					child_path TEXT,
					create_on TEXT,
					file_size TEXT,
					selected INTEGER NOT NULL CHECK (selected IN (0, 1)),
					dtype Text,
					page INTEGER
					)"""
		self.cur.execute("""DROP TABLE IF EXISTS duplicates""")
		self.cur.execute(table)
		self.con.commit()  # Commit changes

	def clear_table(self):
		self.cur.execute("""DROP TABLE IF EXISTS duplicates""")
		self.con.commit()  # Commit changes

	def is_table_empty(self):
		sql = """SELECT COUNT(*) FROM (SELECT 0 FROM duplicates LIMIT 1)"""
		self.cur.execute(sql)
		if self.cur.fetchone()[0] == 0:
			return True
		else:
			return False

	def reset_table(self):
		self.cur.execute("""DELETE from duplicates""")
		self.con.commit()  # Commit changes
		# print(f'Deleted {self.cur.rowcount} records from the SQLite3 database.')

	def close(self):
		# Close cursor & connection
		self.cur.close()
		self.con.close()
		# print(f"Closed SQLITE3 database.")
		# Delete sqlite3 file if it exist
		if self.file.exists():
			self.file.unlink()

	# print(f"Deleted {self.file}.")

	def populate(self, sdir: str, duplicated_photos: dict):
		"""Method to populate sqlite3-database table, called duplicates, with
		info from the found photos with duplicates.
		each row of the database table stores the following info:
			photo item_id, group_id, hashhex, full_path, child_path, create_on,
			file_size, selected, dtype, detached
		"""
		# print(f"\ndef populate(self):")
		# print(f"{sdir=}")
		# print(f"{duplicated_photos=}")
		if not dir:
			raise AttributeError("dir is not defined.")
		elif not Path(sdir).exists():
			raise AttributeError(f"{sdir} does not exist.")
		elif not Path(sdir).is_dir():
			raise AttributeError(f"{sdir} is not a directory.")
		else:
			directory = sdir

		if duplicated_photos:
			counter = count(start=0, step=1)
			sn = next(counter)

			for n, (k, v) in enumerate(duplicated_photos.items()):
				page = n // GROUPS_IN_A_PAGE
				# print(f"{n=}, {page=}")
				hashhex = k
				group_id = f"G{n}"
				# print(f"{v=}")
				dups = sort_photos_by_creation_time(v)  # ascending order
				# print(f"{dups=}")
				for mm, dup in enumerate(dups):
					full_path = str(dup)
					child_path = f".{full_path[len(directory):]}"
					# print(f"{child_path=}")
					item_id = f"{group_id}_F{mm}"
					fsize = filesize(dup.stat().st_size)
					file_size = f"{fsize[0]:.3f} {fsize[1]}"
					ctime = dup.stat().st_ctime
					dtime = datetime.fromtimestamp(ctime)
					create_on = datetime.strftime(dtime, "%Y-%m-%d %H:%M:%S")
					selected = False  # False
					if mm == 0:
						dtype = "Original"
					else:
						dtype = "Copy"
					values = (
						sn, item_id, group_id, hashhex, full_path, child_path,
						create_on, file_size, selected, dtype, page
					)
					self.insert_data_row(values)
					sn = next(counter)

	def get_max_sn_of_group_id(self, group_id: str):
		sql1 = """SELECT MAX(sn) FROM
		          (SELECT sn from duplicates WHERE group_id == (?))"""
		self.cur.execute(sql1, (group_id,))
		num = self.cur.fetchone()[0]
		print(f"{type(num)=} {num=}")
		return num

	def insert_data_row(self, items):
		"""Method to insert a row of data into the table, if they do not
		exist."""
		sql = """INSERT OR IGNORE INTO duplicates VALUES(?,?,?,?,?,?,?,?,?,?,?)
		"""
		self.cur.execute(sql, items)
		self.con.commit()

	def get_group_ids_of_page(self, page: int):
		sql = """SELECT DISTINCT group_id FROM duplicates WHERE page in (?)"""
		self.cur.execute(sql, (page,))
		return [gid[0] for gid in self.cur.fetchall()]

	def get_all_page_numbers(self):
		sql = """SELECT DISTINCT page FROM duplicates"""
		self.cur.execute(sql)
		return [page[0] for page in self.cur.fetchall()]

	def renumber_sn(self):
		self.cur.execute("""SELECT sn, item_id FROM duplicates""")
		results = self.cur.fetchall()
		if results:
			for nn, (sn, iid) in enumerate(results):
				print(nn, sn, iid)
				sql = """UPDATE duplicates SET sn=(?) WHERE item_id=(?)"""
				self.cur.execute(sql, (nn, iid))
			new_sn = self.get_column("sn")
			print(f"{len(new_sn)=} {new_sn=}")

	def get_data_all(self):
		self.cur.execute("""SELECT * FROM duplicates""")
		return self.cur.fetchall()

	def get_group_ids(self):
		self.cur.execute("""SELECT DISTINCT group_id FROM duplicates""")
		return [i[0] for i in self.cur.fetchall()]

	def get_data_rows(self, index, span=100, ):
		sql = """SELECT * FROM duplicates LIMIT (?) OFFSET (?)"""
		self.cur.execute(sql, (span, index,))
		return self.cur.fetchall()

	def get_column(self, column: Literal["sn", "item_id", "group_id",
	"hashhex", "full_path", "child_path", "create_on", "file_size",
	"selected", "dtype"]):
		self.cur.execute(f"SELECT {column} FROM duplicates")
		values = self.cur.fetchall()
		return [i[0] for i in values]

	def get_max_group_index(self):
		self.cur.execute(f"SELECT group_id FROM duplicates")
		group_ids = {int(i[0][1:]) for i in self.cur.fetchall()}
		# print(f"\n{group_ids}")
		if group_ids:
			max_group_ids = f"G{max(group_ids)}"
		else:
			max_group_ids = None
		# print(f"{max_group_ids}\n")
		return max_group_ids

	def get_min_group_index(self):
		self.cur.execute(f"SELECT group_id FROM duplicates")
		group_ids = {int(i[0][1:]) for i in self.cur.fetchall()}
		# print(f"\n{group_ids}")
		if group_ids:
			min_group_ids = f"G{min(group_ids)}"
		else:
			min_group_ids = None
		# print(f"{min_group_ids}\n")
		return min_group_ids

	def get_data_rows_min_group_id(self, index, span=GROUPS_IN_A_PAGE, ):
		sql = """SELECT MIN(group_id) FROM (SELECT group_id FROM duplicates 
		      LIMIT ? OFFSET ?)"""
		self.cur.execute(sql, (span, index,))
		return self.cur.fetchone()[0]

	def get_data_rows_max_group_id(self, index, span=GROUPS_IN_A_PAGE, ):
		sql = """SELECT MAX(group_id) FROM (SELECT group_id FROM duplicates 
				LIMIT ? OFFSET ?)"""
		self.cur.execute(sql, (span, index,))
		return self.cur.fetchone()[0]

	def get_group_items(self, grp_id):
		sql = """SELECT * FROM duplicates WHERE group_id in (?)"""
		self.cur.execute(sql, (grp_id,))
		return self.cur.fetchall()

	def get_item_ids_of_group(self, group_id: str):
		sql = """SELECT item_id	FROM duplicates	WHERE group_id in (?)"""
		self.cur.execute(sql, (group_id,))
		iids = self.cur.fetchall()
		return [iid[0] for iid in iids]

	def get_selected_of_group(self, group_id: str):
		sql = """SELECT selected FROM duplicates WHERE group_id in (?)"""
		self.cur.execute(sql, (group_id,))
		selected = self.cur.fetchall()
		return [sel[0] for sel in selected]

	def get_group_id_of_item(self, item_id: str):
		sql = """SELECT group_id FROM duplicates WHERE item_id in (?)"""
		self.cur.execute(sql, (item_id,))
		return self.cur.fetchone()[0]

	def get_previous_page_of_group_ids(self, group_id: str, span: int):
		sql1 = """SELECT MIN(sn) FROM 
	            (SELECT sn from duplicates WHERE group_id == (?))"""
		sql2 = """SELECT group_id from duplicates 
	            WHERE sn < (?)"""
		self.cur.execute(sql1, (group_id,))
		start_sn = self.cur.fetchone()[0]
		print(f"{start_sn=}")
		self.cur.execute(sql2, (start_sn,))
		indexes = {int(i[0][1:]) for i in self.cur.fetchall()}
		print(f"{indexes=}")
		gids = [f"G{i}" for i in sorted(indexes, reverse=True)[:span]]
		gids.reverse()
		print(f"{gids=}")
		return gids

	def get_next_page_of_group_ids(self, group_id: str, span: int):
		sql1 = """SELECT MAX(sn) FROM 
	            (SELECT sn from duplicates WHERE group_id == (?))"""
		sql2 = """SELECT DISTINCT group_id FROM duplicates
	                WHERE sn > (?) LIMIT (?)"""
		self.cur.execute(sql1, (group_id,))
		start_sn = self.cur.fetchone()[0]
		print(f"{start_sn=}")
		print(f"{span=}")
		self.cur.execute(sql2, (start_sn, span,))
		indexes = {int(i[0][1:]) for i in self.cur.fetchall()}
		print(f"{indexes=}")
		gids = [f"G{i}" for i in sorted(indexes, reverse=False)[:span]]
		# gids.reverse()
		print(f"{gids=}")
		# return [i[0] for i in self.cur.fetchall()]
		return gids

	def get_full_paths_of_group(self, group_id: str):
		sql = """SELECT full_path FROM duplicates WHERE group_id in (?)"""
		self.cur.execute(sql, (group_id,))
		fpaths = self.cur.fetchall()
		return [fpath[0] for fpath in fpaths]

	def get_item(self, item_id):
		"""Method returns data on item_id as a tuple."""
		sql = """SELECT * FROM duplicates WHERE item_id in (?)"""
		self.cur.execute(sql, (item_id,))
		return self.cur.fetchall()[0]

	def get_selected_of_item(self, item_id):
		sql = """SELECT selected FROM duplicates WHERE item_id in (?)"""
		self.cur.execute(sql, (item_id,))
		return self.cur.fetchone()[0]

	def get_selected_of_dtype(self, dtype: Literal["Original", "Copy"]):
		sql = """SELECT selected FROM duplicates WHERE dtype in (?)"""
		self.cur.execute(sql, (dtype,))
		values = self.cur.fetchall()
		return [i[0] for i in values]

	def get_selected(self, value: bool = True):
		"""Method returns a dict of the iid and full-path of the selected
		items."""
		sql = """SELECT item_id, full_path FROM duplicates 
		         WHERE selected in (?)"""
		self.cur.execute(sql, (value,))
		selected = {i[0]: i[1] for i in self.cur.fetchall()}
		return selected

	def get_fiid_giid_fpath_of_selected(self, value: bool = True):
		sql = """SELECT item_id, group_id, full_path FROM duplicates
		         WHERE selected in (?)"""
		self.cur.execute(sql, (value,))
		selected = {i[0]: [i[1], i[2]] for i in self.cur.fetchall()}
		return selected

	def get_last_group_id(self):
		self.cur.execute("""SELECT group_id FROM duplicates ORDER BY sn DESC 
		LIMIT 1""")
		return self.cur.fetchone()[0]

	def toggle_all_selected_of_dtype(self, dtype: str):
		"""Method to toggle the value of the 'selected' column of the
		`duplicate` table."""
		if dtype not in ("Original", "Copy"):
			raise ValueError("The value of 'dtype' must be either 'Original'"
							 " or 'Copy'.")
		sql = """UPDATE duplicates
				SET selected = CASE selected
								WHEN 0 THEN 1 
								ELSE 0 END
				WHERE dtype = ?"""
		self.cur.execute(sql, (dtype,))
		self.con.commit()

	def toggle_selected_of_item(self, item_id: str):
		"""Method to toggle the value of the 'selected' column of one item in
		the `duplicate` table."""
		sql = """UPDATE duplicates
				SET selected = CASE selected
								WHEN 0 THEN 1 
								ELSE 0 END
				WHERE item_id = ?"""
		self.cur.execute(sql, (item_id,))
		self.con.commit()

	def toggle_selected_of_items(self, item_ids: list):
		"""Method to toggle the value of the 'selected' column of the
		`duplicate` table."""
		sql = """UPDATE duplicates
				SET selected = CASE selected
								WHEN 0 THEN 1 
								ELSE 0 END
				WHERE item_id = ?"""
		self.cur.executemany(sql, item_ids)
		self.con.commit()

	def set_selected_of_dtype(self, dtype: Literal["Original", "Copy"],
							  value: Literal['0', '1']):
		"""Method to set the selected column to True or False of row(s) where
		dtype is either "Original" or "Copy"."""
		if dtype not in ("Original", "Copy"):
			raise ValueError("The value of 'dtype' must be either 'Original'"
							 " or 'Copy'.")
		if value not in ("0", "1"):
			raise ValueError("The value of 'value' must be either str type "
							 "'0' or '1'.")
		sql = f"UPDATE duplicates SET selected = {value} WHERE dtype = ?"
		self.cur.execute(sql, (dtype,))
		self.con.commit()

	def delete_fiid(self, fiid: str):
		sql = """DELETE FROM duplicates WHERE item_id in (?)"""
		self.cur.execute(sql, (fiid,))
		self.con.commit()


if __name__ == "__main__":
	source = str(CWD / "Samples" / "Photos4")
	duplicates = {
		'6035a204bc4beea6ae4e539b0ef76ef8bc5fd1e1c7c6ba3e9711d941a47386c3': {
			source + '/Wallpapers_old/Apartments/maxresdefault.jpg',
			source + '/Wallpapers/Apartments/maxresdefault.jpg'},
		'0f224df4d0c8d0eb5c80b329e3109f4622a2156b7c134787c8caed1ce1c7d692': {
			source + '/Wallpapers/Apartments/Clean-Apartment-Interior-Design'
					 '.jpeg',
			source + '/Wallpapers/Apartments/Clean-Apartment-Interior-Design'
					 '-2.jpeg',
			source + '/Wallpapers_old/Apartments/Clean-Apartment-Interior'
					 '-Design.jpeg',
			source + '/Wallpapers_old/Apartments/Clean-Apartment-Interior'
					 '-Design-2.jpeg'},
		'6cc08b13d0b0c2bc8716f600003f3f83af81e9d513d10cdf240144f0ef6bc825': {
			source + '/Wallpapers/blue_dwell_in_possibility.jpg',
			source + '/Wallpapers_old/blue_dwell_in_possibility.jpg'},
		'6539177353859ce846a90e067fac850c6196dca3420b08fb8dd751432c0e18b8': {
			source + '/Wallpapers/Apartments/MPM94144.jpg',
			source + '/Wallpapers_old/Apartments/MPM94144.jpg'},
		'64575ec8e1ff28f7bc071243350c8bfa51b8dd727a142581f43dd93c6d96e4b3': {
			source + '/Wallpapers_old/Apartments/98758711.jpg',
			source + '/Wallpapers/Apartments/98758711.jpg'},
		'7e4e229ea05b5767f474759f169cb18935cd6108f65811b0b9431d1f11a5c7a7': {
			source + '/Wallpapers_old/869984-pine-tree-wallpaper.jpg',
			source + '/Wallpapers/869984-pine-tree-wallpaper.jpg'},
		'08387d3167070ffb50c96dd53f14caf0d19576bf038c62c8d45620baa0fa5f8b': {
			source + '/Wallpapers_old/beach.jpg',
			source + '/Wallpapers/beach.jpg'},
		'fb5481bc2b623779bdeaa2f90bd9d60557eca3dbcde35a93a71fd9fcf9798dfa': {
			source + '/Wallpapers_old/HighSierra-wallpapers/Sierra.jpg',
			source + '/Wallpapers/HighSierra-wallpapers/Sierra.jpg'},
		'307ba13e4521f631941e90c468c4899b9c28e98c45a5b9e98d19d7f98e20ea05': {
			source + '/Wallpapers_old/HighSierra-wallpapers/High Sierra.jpg',
			source + '/Wallpapers/HighSierra-wallpapers/High Sierra.jpg'},
		'a9b4396d01006fcfe02ea516b5f21f7ab02c2bd643fe3f8197ecaa5de3dd8800': {
			source + '/Wallpapers/blue-dna-molecular-structure.png',
			source + '/Wallpapers_old/blue-dna-molecular-structure.png'},
		'b0a33cfd3cb9968456614fa588c36c2612fb765ee0641cd4444bdd3e230377de': {
			source + '/Wallpapers_old/Apartments/pebbles-apartments-nice'
					 '-living-area-p.webp',
			source + '/Wallpapers/Apartments/pebbles-apartments-nice-living'
					 '-area-p.webp'},
		'eeb5b5f0dd46c9c3f71500e4bbbde72b234bc9326deca5404e85d57e42bf0837': {
			source + '/Wallpapers_old/apple-september-2019-event-1920x1080-4k'
					 '-22059.jpg',
			source + '/Wallpapers/apple-september-2019-event-1920x1080-4k'
					 '-22059.jpg',
			source + '/Wallpapers/apple-september-2019-event-1920x1080-4k'
					 '-22059 (copy).jpg',
			source + '/Wallpapers_old/apple-september-2019-event-1920x1080-4k'
					 '-22059 (copy).jpg'},
		'4620cdb971c9b722e2836dd13695bd7daaba1c79302e4eb80a870d56c033a825': {
			source + '/Wallpapers/demo/copy.jpg',
			source + '/Wallpapers_old/demo/dog-1920x1080-puppy-white-animal'
					 '-pet-beach-sand-sea-1611.jpg',
			source + '/Wallpapers_old/demo/copy.jpg',
			source + '/Wallpapers/demo/dog-1920x1080-puppy-white-animal-pet'
					 '-beach-sand-sea-1611.jpg'},
		'aea4dfdb61613dece386929ef39942fbcf4e75b0192b178ada5b1aa095480b26': {
			source + '/Wallpapers/demo/Sierra2.jpg',
			source + '/Wallpapers/HighSierra-wallpapers/Sierra 2.jpg',
			source + '/Wallpapers_old/demo/Sierra2.jpg',
			source + '/Wallpapers_old/HighSierra-wallpapers/Sierra 2.jpg'},
		'6bc6e42f0e97ecea95b629386840c78e15d46c8fa7e6897bbbcfc977119c8326': {
			source + '/Wallpapers/dmb_mountain_blue.jpg',
			source + '/Wallpapers_old/dmb_mountain_blue.jpg'},
		'3139e97f8d4632e52f3e1a85e0d02812ed152abc4a704a646815ce8e3f247794': {
			source + '/Wallpapers_old/Zoom/room.jpg',
			source + '/Wallpapers/Zoom/room.jpg'},
		'7775518190fa2bbd89db979d640407f8e22ac30b8350485b35ae16967cc8296d': {
			source + '/Wallpapers_old/blue_sea_boardwalk.jpg',
			source + '/Wallpapers/blue_sea_boardwalk.jpg'},
		'0b1f83303887604e55e24b81033ea08a9b2d920054e493717db6ef051adc69c8': {
			source + '/Wallpapers_old/dmb_mountain_scene.jpg',
			source + '/Wallpapers/dmb_mountain_scene.jpg'},
		'7aa32c2a2d0a0477f4ea5db0f4f5cc85f47e94fe3772742bd28f1351f535f9b2': {
			source + '/Wallpapers_old/demo/Milaidhoo-Island-Maldives-Beach'
					 '-Bedroom-Feat.jpg',
			source + '/Wallpapers_old/Milaidhoo-Island-Maldives-Beach-Bedroom'
					 '-Feat.jpg',
			source + '/Wallpapers/Milaidhoo-Island-Maldives-Beach-Bedroom'
					 '-Feat.jpg',
			source + '/Wallpapers/demo/Milaidhoo-Island-Maldives-Beach'
					 '-Bedroom-Feat.jpg'},
		'18f8f411c14eba2dc3e64d7c250542d1a1994854363a495411660a7a7dc79961': {
			source + '/Wallpapers_old/dandelion-1920x1080_flower_zoom.jpg',
			source + '/Wallpapers/dandelion-1920x1080_flower_zoom.jpg'},
		'61bf6d7ee48fc4bf9693346af49d34e05b5133c1e27d31caf8d5c488b5508d91': {
			source + '/Wallpapers/dmb_earth.jpg',
			source + '/Wallpapers_old/dmb_earth.jpg'},
		'798c83a6255ed02acba4648e8979db3761763e7d2a92a0a6b2e850ce977a3946': {
			source + '/Wallpapers_old/blue_wallpaper.jpg',
			source + '/Wallpapers/blue_wallpaper.jpg'},
		'03edf41b6b06ffea2b6457ba7b6d5d6ec8563358022ecd21afc65a2181c20f79': {
			source + '/Wallpapers/dmb_pexels-pixabay-459261.jpg',
			source + '/Wallpapers_old/dmb_pexels-pixabay-459261.jpg'},
		'72429aa324257e4f032fc5ed5a166a53e7b4fbb478cc4f585a8f2b925c488b73': {
			source + '/Wallpapers/dmb_art.jpg',
			source + '/Wallpapers_old/dmb_art.jpg'},
		'9b9074ef728d700380354eab8821cfc2995971cf88c32bf4df907f16afa13a8d': {
			source + '/Wallpapers/Blue_honeycomb.jpg',
			source + '/Wallpapers_old/Blue_honeycomb.jpg'},
		'bb149fac4f236ce430e3e744880d09dfdd2c2dd2d0d3c0cf0f70d6ea23253dad': {
			source + '/Wallpapers/dmb_Gollinger_Wasserfall_Austria.jpg',
			source + '/Wallpapers_old/dmb_Gollinger_Wasserfall_Austria.jpg'},
		'c33810e9dde7206e74d73b541173418cac0688286a85ebbe7d273b84ca6036bd': {
			source + '/Wallpapers_old/dmb_7006190-4k.jpg',
			source + '/Wallpapers/dmb_7006190-4k.jpg'},
		'5850dcb91d40b6cd6b086a426199f98e6ba9c5d87fbc57309b4f2d7ced92153c': {
			source + '/Wallpapers_old/blue_magenta.jpg',
			source + '/Wallpapers/blue_magenta.jpg'},
		'8fd9d0920e910253ca6007e983b294d651807266934f72b3e1378b0751890f24': {
			source + '/Wallpapers_old/dandelion-1920x1080_flower.jpg',
			source + '/Wallpapers/dandelion-1920x1080_flower.jpg'},
		'743fcb7755a94317069a0dc07eb7e88a7fc4a6b78dfd80d4296ae6fec3b9b81c': {
			source + '/Wallpapers/dmb_monument_valley.jpg',
			source + '/Wallpapers_old/dmb_monument_valley.jpg'},
		'f0f0cecc7f56e2d3f840455e7439f09a5b736b151265e4404b27c8784afb7dfe': {
			source + '/Wallpapers_old/lake-tekapo-1920x1080-new-zealand'
					 '-mountains-sky-clouds-8k-16351.jpg',
			source + '/Wallpapers/lake-tekapo-1920x1080-new-zealand-mountains'
					 '-sky-clouds-8k-16351.jpg'},
		'b14dafa7c37d95571968178b70ec4cbb822619d4bc936ffcb52ae47eb686beb0': {
			source + '/Wallpapers_old/Modern-Living-Rooms_13.jpg',
			source + '/Wallpapers/Modern-Living-Rooms_13.jpg'},
		'3fa31c8fb9a569a19d3194cc69ece0878a08274fde2d69c9afa6752354b6926e': {
			source + '/Wallpapers_old/dmb_neuronspiketrain.jpg',
			source + '/Wallpapers/dmb_neuronspiketrain.jpg'},
		'b139b508d67a57d471347a501a7d24ea6c88ec8a0414c1894bd9fa5c7414be6a': {
			source + '/Wallpapers_old/dmb_earth_from_space.jpg',
			source + '/Wallpapers/dmb_earth_from_space.jpg'},
		'6ec0002b32a9744ecb48185c4d0b0bcfa0f508de1d1711bd0f3eee13544dd70f': {
			source + '/Wallpapers/dmb_199836.jpg',
			source + '/Wallpapers_old/dmb_199836.jpg'},
		'14a6862a62d185d8389ab27b9ab9f6b69920c15836a791f4504c28323b16ce33': {
			source + '/Wallpapers_old/dmb_San_Francisco.jpg',
			source + '/Wallpapers/dmb_San_Francisco.jpg'},
		'5e6cd4106791983b24789b55c23158b75d7465d80177d89fe90af4907e62fe81': {
			source + '/Wallpapers/coa2022.jpeg',
			source + '/Wallpapers_old/coa2022.jpeg'},
		'62979f996a2c7ec44d64c9b2a29b252b138bffb8a23036bbe46f758209a99d46': {
			source + '/Wallpapers_old/blue_whaleshark.jpg',
			source + '/Wallpapers/blue_whaleshark.jpg'},
		'970e1358d7a6ecb5c5c91709fb8641826619d9dae5b28fdc4d7b1549dca073a3': {
			source + '/Wallpapers_old/dmb_pexels-pixabay-358482.jpg',
			source + '/Wallpapers/dmb_pexels-pixabay-358482.jpg'},
	}

	db = DuplicatesDB()
	print(f"\n{db.is_table_empty()=} {type(db.is_table_empty())=}")
	index = [i for i in range(len(duplicates))]
	print(f"\n{db.is_table_empty()=}")
	db.populate(source, duplicates)

	print(f"\n{db.is_table_empty()=}")

	g_selected = db.get_selected_of_group("G1")
	print(f"\n{type(g_selected)=} {g_selected=}")

	db.close()
