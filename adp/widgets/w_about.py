# print(f"{__name__}")

# Python modules
import tkinter as tk
import tkinter.ttk as ttk
import webbrowser
from functools import partial

# External Packages
from PIL import Image, ImageTk

# Project modules
from adp.widgets.constants import BG, FG, DFONT, CWD
from adp.widgets.w_tkHyperlinkManager import HyperlinkManager
from adp.widgets.w_tools import get_geometry_values, str_geometry_values

__all__ = ["About"]
__version__ = '0.1.1'
__license__ = "Apache License, Version 2.0"
__copyright__ = "Copyright 2024, Chia Yan Hon, Julian."
__author__ = 'Chia Yan Hon, Julian.'
__email__ = "julianchiayh@gmail.com"


class About(ttk.Frame):
    """A custom widget to show information about the ADP GUI."""
    def __init__(self, master,  **options):
        try:
            align = options.pop("align")
        except KeyError:
            self.align = "left"  # default value
        else:
            if align in ["left", "right"]:
                self.align = align
            else:
                raise ValueError(f"align={align} is invalid. It's value must "
                                 f"either be 'left' or 'right'.")
        super().__init__(master, **options)
        self.master = master
        self.bn_copyright = None
        self.bn_source = None
        self.license = None
        self.license_text = None
        self.license_hyperlink = None
        self.license_bn_close = None

        i1 = Image.open(str(CWD) + '/icons/adp/ADP_icon_32.png')
        self.icon = ImageTk.PhotoImage(i1)
        self.icon.image = i1

        self._create_widgets()
        self._create_bindings()

    def _create_widgets(self):
        # Copyright and source buttons
        # cr = f"Copyright © 2024, Chia Yan Hon, Julian."
        self.bn_copyright = ttk.Button(self, style="About.TButton",
                                       # text=cr, compound='left',
                                       image=self.icon)
        self.bn_copyright.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        # License window - toplevel
        dfont = list(DFONT.values())
        self.license = tk.Toplevel(bg=BG)
        self.license.title("License")
        self.license_text = tk.Text(self.license, wrap=tk.WORD, fg=BG, bg=FG,
                                    selectbackground=FG, selectforeground=BG,
                                    width=72, height=15, borderwidth=1,
                                    relief='sunken', font=dfont,
                                    )
        self.license_hyperlink = HyperlinkManager(self.license_text)
        self.bn_source = ttk.Button(self.license, text="Source Code",
                                    style="About.TButton",
                                    command=self._show_sourcecode)
        self.license_bn_close = ttk.Button(self.license, text="Close",
                                           style="About.TButton",
                                           command=self._close_license)

        self.license_text.grid(row=0, column=0, columnspan=2, sticky="nsew",
                               padx=10, pady=10)
        self.bn_source.grid(row=1, column=0, sticky="nsew", padx=20,
                            pady=(0, 10))
        self.license_bn_close.grid(row=1, column=1, sticky="nsew", padx=20,
                                   pady=(0, 10))

        msgs = [
            f'\n',
            f'  Copyright 2024, Chia Yan Hon, Julian.\n',
            f'\n',
            f'  Licensed under the Apache License, Version 2.0 (the '
            f'"License");\n',
            f'  you may not use this file except in compliance with the '
            f'License.\n',
            f'  You may obtain a copy of the License at\n',
            f'\n',
            f'  http://www.apache.org/licenses/LICENSE-2.0\n',
            f'\n',
            f'  Unless required by applicable law or agreed to in writing,'
            f' software\n',
            f'  distributed under the License is distributed on an "AS IS" '
            f'BASIS,\n',
            f'  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express '
            f'or implied.\n',
            f'  See the License for the specific language governing permissions'
            f' and \n',
            f'  limitations under the License.',
            f'\n',
        ]
        for n, msg in enumerate(msgs):
            if n == 7:
                self.license_text.insert(
                    "end",
                    msg,
                    self.license_hyperlink.add(
                        partial(
                            webbrowser.open,
                            "https://www.apache.org/licenses/LICENSE-2.0",
                        )
                    )
                )
            else:
                self.license_text.insert("end", msg)
        self.license_text.config(state="disabled")  # Prevent changes
        license = self.license
        license.overrideredirect(False)
        license.transient(master=self.master.winfo_toplevel())
        license.resizable(width=None, height=None)  # Non-resizable
        license.update_idletasks()
        license.protocol('WM_DELETE_WINDOW', self._close_license)
        self.license_geometry = get_geometry_values(license.winfo_geometry())
        license.withdraw()  # Hide the window.

    def _create_bindings(self):
        self.bn_copyright.bind("<Button-1>", self._show_license)

    def _show_license(self, event):
        """Position self.license directly above self.bn_copyright, disable
        self.bn_copyright and make root window widgets unresponsive.

        geom is ('wxh±x±y')
        """
        # Get geometry of widgets
        widget_master = event.widget.master
        widget_toplevel = event.widget.winfo_toplevel()
        l_geo = self.license_geometry
        w_geo = get_geometry_values(event.widget.winfo_geometry())
        wm_geo = get_geometry_values(widget_master.winfo_geometry())
        wtl_geo = get_geometry_values(widget_toplevel.winfo_geometry())

        # New width, height, x, y of self.license
        wm_decorator_height = 40
        new_y = (wtl_geo[3] + wtl_geo[1] - wm_geo[1] - l_geo[1] -
                 wm_decorator_height)

        def align_top_left():
            return str_geometry_values(l_geo[0], l_geo[1], wtl_geo[2], new_y)

        def align_top_right():
            new_x = wtl_geo[0] + wtl_geo[2] - l_geo[0] - 12
            return str_geometry_values(l_geo[0], l_geo[1], new_x, new_y)

        match self.align:
            case "left":
                license_new_geom = align_top_left()
            case "right":
                license_new_geom = align_top_right()

        # Configure appearance of self.bn_copyright, self.license & root
        widget = event.widget  # is self.bn_copyright
        widget.state(["disabled", '!active', "!pressed"])
        self.master.winfo_toplevel().resizable(width=False, height=False)
        license = self.license
        license.deiconify()  # unhide self.license
        license.geometry(license_new_geom)  # at new location
        license.grab_set()  # grabs all events; root's widgets are unresponsive
        license.update_idletasks()

    def _close_license(self):
        self.license.grab_release()
        self.license.withdraw()
        self.bn_copyright.state(["!disabled"])
        self.master.winfo_toplevel().resizable(width=True, height=True)

    @staticmethod
    def _show_sourcecode():
        url = f"https://github.com/JulianChia/adp"
        webbrowser.open_new(url)


if __name__ == "__main__":
    from adp.widgets import customise_ttk_widgets_style

    root = tk.Tk()
    s = ttk.Style()
    style = customise_ttk_widgets_style(s)
    app = About(root, style='About.TFrame')
    app.grid(row=0, column=0, sticky="se")
    root.mainloop()
