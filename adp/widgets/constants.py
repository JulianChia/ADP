# print(f"{__name__}")

# Colours
BG = '#3b3b39'
BG2 ='#17090b'
FG = 'white'
PB_THICKNESS = 5  # pixels
PB_COLOR = "#e35d18"
C0 = "#e35d18"
C0_light = "#ee8c5a"
C0_dark = "#9e4111"
D1_C0 = "yellow"
# D1_C1 = "#e35d18"
D1_C1 = "grey"
D1_C2 = "orange"
# D1_C2 = "#18e35d"
D2_C1 = "#18e35d"
# D2_C1 = "orange"
D2_C2 = "#189ee3"
RING1 = {'color0': D1_C0, 'color1': D1_C1, 'color2': D1_C2}
RING2 = {'color0': D1_C2, 'color1': D2_C1, 'color2': D2_C2}

# Fonts
DFONT = dict(family='URW Gothic L', size=11, weight='normal')
BFONT = dict(family='URW Gothic L', size=11, weight='bold')
TFONT = dict(family='URW Gothic L', size=12, weight='bold')

MSG0 = f' TO START: 1. Click Folder  2. Click Find.'
GROUPS_IN_A_PAGE = 20

# Python modules
from pathlib import Path
HOME = Path.home()
CWD = Path(__file__).parent.parent
# print(f'{HOME=}')
# print(f'{CWD=}')

__all__ = ["BG", "BG2", "FG", "PB_THICKNESS", "PB_COLOR", "C0", "C0_light",
           "C0_dark", "D1_C0", "D1_C1", "D1_C2", "D2_C1", "D2_C2", "RING1",
	   	   "RING2", "DFONT", "BFONT", "TFONT", "MSG0",  "GROUPS_IN_A_PAGE",
		   "HOME", "CWD"]
	   
