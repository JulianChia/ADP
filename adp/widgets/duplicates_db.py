# Python modules
import sqlite3
from datetime import datetime
from pathlib import Path
from itertools import count
from typing import Literal

# Project modules
from adp.widgets.constants import CWD, GROUPS_IN_A_PAGE
from adp.functions.tools import sort_pictures_by_creation_time, filesize

__all_ = ["DuplicatesDB"]
__version__ = '0.1.1'
__license__ = "Apache License, Version 2.0"
__copyright__ = "Copyright 2024, Chia Yan Hon, Julian."
__author__ = 'Chia Yan Hon, Julian.'
__email__ = "julianchiayh@gmail.com"


class DuplicatesDB:
	"""Class to create a SQLITE3 database to store picture duplicates info."""

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

	def populate(self, sdir: str, duplicated_pictures: dict):
		"""Method to populate sqlite3-database table, called duplicates, with
		info from the found pictures with duplicates.
		each row of the database table stores the following info:
			picture item_id, group_id, hashhex, full_path, child_path, create_on,
			file_size, selected, dtype, detached
		"""
		# print(f"\ndef populate(self):")
		# print(f"{sdir=}")
		# print(f"{duplicated_pictures=}")
		if not dir:
			raise AttributeError("dir is not defined.")
		elif not Path(sdir).exists():
			raise AttributeError(f"{sdir} does not exist.")
		elif not Path(sdir).is_dir():
			raise AttributeError(f"{sdir} is not a directory.")
		else:
			directory = sdir

		if duplicated_pictures:
			counter = count(start=0, step=1)
			sn = next(counter)

			for n, (k, v) in enumerate(duplicated_pictures.items()):
				page = n // GROUPS_IN_A_PAGE
				# print(f"{n=}, {page=}")
				hashhex = k
				group_id = f"G{n}"
				# print(f"{v=}")
				dups = sort_pictures_by_creation_time(v)  # ascending order
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

# if __name__ == "__main__":
# 	from adp.functions.picture_finder_concurrent import fast_scandir, scandir_images_concurrently
# 	from adp.functions.duplicates_finder_concurrent import detect_duplicates_concurrently
#
# 	source = str(CWD.parent / "Samples" / "Photos4")
# 	subdirs = fast_scandir(source)
# 	pictures = scandir_images_concurrently([source] + subdirs, cfe="process")
# 	duplicates = detect_duplicates_concurrently(pictures, cfe="process")
#
# 	db = DuplicatesDB()
# 	print(f"\n{db.is_table_empty()=} {type(db.is_table_empty())=}")
# 	index = [i for i in range(len(duplicates))]
# 	print(f"\n{db.is_table_empty()=}")
# 	db.populate(source, duplicates)
#
# 	print(f"\n{db.is_table_empty()=}")
#
# 	g_selected = db.get_selected_of_group("G1")
# 	print(f"\n{type(g_selected)=} {g_selected=}")
#
# 	db.close()
