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
	name for name in dir()
	if not name.startswith('_') and name not in exclude and 'w_' not in name
]
# print(f"widgets {__all__=}")

"""
From modules in widgets directory
Classes - HyperlinkManager
          Findings
          RingsChart
          Progressbarwithblank
          Find
          AutoScrollbar
          VerticalScrollFrame
          DupGroup
          Table
          Gallery
          About
          AnyDuplicatedPhotos
Functions - customise_ttk_widgets_style
            stylename_elements_options
            string_pixel_size
            get_geometry_values
            str_geometry_values
            run_adp 
            main
            
Notes: 
1. Widgets `Findings` and `RingsChart` are used to make the `Find` widget.
2. Widgets `AutoScrollbar`, `VerticalScrollFrame`, `DupGroup` and `Table` are
   used to make the `Gallery` widget.
3. Widgets `Find` and `Gallery` are used to make the `AnyDuplicatedPhotos`
   widget.
"""