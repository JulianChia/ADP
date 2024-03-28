# print(f"{__name__}")

# Import from modules in widgets directory
from adp.widgets.w_ttkstyle import *
from adp.widgets.w_tools import *
from adp.widgets.w_tkHyperlinkManager import *
from adp.widgets.w_about import *
from adp.widgets.w_progressbar import *
from adp.widgets.w_dupgroups import *
from adp.widgets.w_findindicators import *
from adp.widgets.w_find import *
from adp.widgets.w_scrframe import *
from adp.widgets.w_table import *
from adp.widgets.w_gallery import *
from adp.widgets.w_adp import *

exclude = ["exclude", "widgets", "constants", "duplicates_db"]

__all__ = [
	name for name in dir() if not name.startswith('_') and name not in exclude
]
# print(f"widgets {__all__=}")
