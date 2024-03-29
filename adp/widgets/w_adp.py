# print(f"{__name__}")

# Python modules
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
import argparse

# External Packages
from PIL import ImageTk

# Project module
from adp.widgets.constants import CWD, BG
from adp.widgets.w_ttkstyle import customise_ttk_widgets_style
from adp.widgets.w_find import Find
from adp.widgets.w_table import Table
from adp.widgets.w_gallery import Gallery
from adp.widgets.w_about import About

__all__ = ["ADPFind", "ADPTable", "ADPGallery", "ADP", "main"]
__version__ = '0.1'
__author__ = 'Chia Yan Hon, Julian.'
__copyright__ = "Copyright 2024, Chia Yan Hon, Julian."
__license__ = "Apache License, Version 2.0"


class ADPFind(ttk.Frame):
    """A Tkinter GUI to quickly find duplicated photos.

    ADP = Any Duplicated Photos

    kwargs:
        cfe - concurrent.future.Executor. Its value is either "process" or
              "thread". Default is "process".

    Widget's Roles:
    self: Create and display the Find, About widgets.
    Find: Let user choose a directory and searches it and its children
          directories for duplicated photos. Its search result is store in a
          sqlite3 database.
    About: Display the Copyright, License and sources code of this program.
    """

    def __init__(self, master, **options):
        try:
            cfe = options.pop("cfe")
        except KeyError:
            self.cfe = "process"  # default value
        else:
            if cfe in ["process", "thread"]:
                self.cfe = cfe
            else:
                raise ValueError(f"cfe={cfe} is invalid. It's value must "
                                 f"either be 'process' or 'thread'.")
        super().__init__(master, **options)
        self.master = master
        self._create_widgets()

    def _create_widgets(self):
        self.find = Find(self, layout="vertical", cfe=self.cfe)
        self.about = About(self, align="left", style="About.TFrame")

        self.find.grid(row=0, column=0, sticky="nsew", padx=5, pady=(5, 10))
        self.about.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.winfo_toplevel().minsize(width=420, height=480)

    def exit(self):
        self.find.exit()


class ADPTable(ttk.Frame):
    """A Tkinter GUI to find and delete duplicated photos.

    ADP = Any Duplicated Photos,

    kwargs:
        cfe - concurrent.future.Executor. Its value is either "process" or
              "thread". Default is "process".
        layout - Either "horizontal" or "vertical". Default is "vertical".

    Widget's Roles:
    self: Create and display the Find, Gallery and About widgets and bind the
          events of these widgets.
    Find: Let user choose a directory and searches it and its children
          directories for duplicated photos. Its search result is store in a
          sqlite3 database.
    Table: - Display the search result from the Find widget in a text-based
             scrollable ttk.Treeview widget.
           - Allow selection and deselection of single or multiple photo file
             item(s) and the deletion of these selected photos.
    About: Display the Copyright, License and sources code of this program.
    """

    def __init__(self, master, **options):
        try:
            cfe = options.pop("cfe")
        except KeyError:
            self.cfe = "process"  # default value
        else:
            if cfe in ["process", "thread"]:
                self.cfe = cfe
            else:
                raise ValueError(f"cfe={cfe} is invalid. It's value must "
                                 f"either be 'process' or 'thread'.")
        try:
            layout = options.pop("layout")
        except KeyError:
            self.layout = "vertical"  # default value
        else:
            if layout in ["horizontal", "vertical"]:
                self.layout = layout
            else:
                raise ValueError(f"layout={layout} is invalid. It's value must "
                                 f"either be 'horizontal' or 'vertical'.")
        super().__init__(master, **options)
        self.master = master
        self._create_widgets()
        self._create_bindings()

    def _create_widgets(self):
        self.find = Find(self, layout=self.layout, cfe=self.cfe)
        self.find.hide_selected_path()

        self.table = Table(self)
        self.table.set_sdir(self.find.selected_dir)
        self.table.set_sql3db(self.find.sqlite3_db)

        if self.layout in "vertical":
            align = "left"
        elif self.layout in "horizontal":
            align = "right"
        self.about = About(self, align=align, style="About.TFrame")

        self.find.grid(row=0, column=0, sticky="nsew", padx=5, pady=(5, 10))
        if self.layout in "vertical":
            self.table.grid(row=0, column=1, sticky="nsew", padx=(0, 5))
            self.about.grid(row=1, column=0, columnspan=2, sticky="nsew")
            self.columnconfigure(1, weight=1)
            self.rowconfigure(0, weight=1)
            self.winfo_toplevel().minsize(width=800, height=500)
        elif self.layout in "horizontal":
            self.table.grid(row=1, column=0, sticky="nsew", padx=5)
            self.about.grid(row=2, column=0, sticky="nse", padx=5)
            self.columnconfigure(0, weight=1)
            self.rowconfigure(1, weight=1)
            self.winfo_toplevel().minsize(width=1200, height=600)

    def _create_bindings(self):
        self.find.unbind("<<DirectorySelected>>")
        self.find.bind("<<DirectorySelected>>", self.event_reset)
        self.find.bind("<<Sqlite3DBPopulated>>",
                       self.table.event_populate_tree_the_first_time)
        self.table.bn_delete.bind("<<DeletionDone>>", self.event_recheck)

    def event_reset(self, event):
        # print(f"\ndef event_reset(self, event):")
        # 2. Reset Table
        if self.table.tree.get_children():
            # print(f"Reset table")
            self.table.reset_table()
        self.table.set_tree_column0_heading_text(self.table.sdir.get())
        # 1. Enable find button
        self.find.bn_find.instate(["disabled"], self.find.enable_find_button)

    def event_recheck(self, event):
        # print(f"\ndef event_recheck(self, event):")
        self.find.reset()
        self.event_reset(event)
        self.find.bn_find.invoke()

    def exit(self):
        self.find.exit()


class ADPGallery(ttk.Frame):
    """A Tkinter GUI to find and delete duplicated photos.

    ADP = Any Duplicated Photos,

    kwargs:
        cfe - concurrent.future.Executor. Its value is either "process" or
              "thread". Default is "process".
        layout - Either "horizontal" or "vertical". Default is "horizontal".

    Widget's Roles:
    self: Create and display the Find, Gallery and About widgets and bind the
          events of these widgets.
    Find: Let user choose a directory and searches it and its children
          directories for duplicated photos. Its search result is store in a
          sqlite3 database.
    Gallery: - Display the search result from the Find widget in its Table
               widget and in a scrollable Viewport.
             - Allow selection and deselection of single or multiple photo file
               item(s) and the deletion of these selected photos.
    About: Display the Copyright, License and sources code of this program.
    """

    def __init__(self, master, **options):

        # 1. Define attributes etype, layout and orient
        try:
            cfe = options.pop("cfe")
        except KeyError:
            self.cfe = "process"  # default value
        else:
            if cfe in ["process", "thread"]:
                self.cfe = cfe
            else:
                raise ValueError(f"cfe={cfe} is invalid. It's value must "
                                 f"either be 'process' or 'thread'.")
        try:
            layout = options.pop("layout")
        except KeyError:
            self.layout = "horizontal"  # default value
        else:
            if layout in ["horizontal", "vertical"]:
                self.layout = layout
            else:
                raise ValueError(f"layout={layout} is invalid. It's value must "
                                 f"either be 'horizontal' or 'vertical'.")
        finally:
            match self.layout:
                case "vertical":
                    self.orient = "vertical"
                case "horizontal":
                    self.orient = "horizontal"

        super().__init__(master, **options)
        self.master = master
        self._create_widgets()
        self._create_bindings()

    def _create_widgets(self):
        self.find = Find(self, layout=self.layout, cfe=self.cfe)
        self.find.hide_selected_path()

        self.gallery = Gallery(self, orient=self.orient)
        table = self.gallery.table
        table.set_sdir(self.find.selected_dir)
        table.set_sql3db(self.find.sqlite3_db)

        if self.layout in "vertical":
            align = "left"
        elif self.layout in "horizontal":
            align = "right"
        self.about = About(self, align=align, style="About.TFrame")

        self.find.grid(row=0, column=0, sticky="nsew", padx=5, pady=(5, 10))
        if self.layout in "vertical":
            self.gallery.grid(row=0, column=1, sticky="nsew", padx=(0, 5))
            self.about.grid(row=1, column=0, columnspan=2, sticky="nsew")
            self.columnconfigure(1, weight=1)
            self.rowconfigure(0, weight=1)
            self.winfo_toplevel().minsize(width=1000, height=600)
        elif self.layout in "horizontal":
            self.gallery.grid(row=1, column=0, sticky="nsew", padx=5)
            self.about.grid(row=2, column=0, sticky="nse", padx=5)
            self.columnconfigure(0, weight=1)
            self.rowconfigure(1, weight=1)
            self.winfo_toplevel().minsize(width=1200, height=500)

    def _create_bindings(self):
        find = self.find
        table = self.gallery.table

        find.unbind("<<DirectorySelected>>")
        find.bind("<<DirectorySelected>>", self.event_reset)
        find.bind("<<Sqlite3DBPopulated>>",
                  table.event_populate_tree_the_first_time)
        table.bn_delete.bind("<<DeletionDone>>", self.event_recheck)

    def event_reset(self, event):
        # print(f"\ndef event_reset(self, event):")
        # 2. Reset Table
        table = self.gallery.table
        if table.tree.get_children():
            # print(f"Reset table")
            table.reset_table()
        self.after_idle(table.set_tree_column0_heading_text, table.sdir.get())
        self.gallery.update_idletasks()
        # 1. Enable find button
        self.after_idle(self.find.enable_find_button)

    def event_recheck(self, event):
        # print(f"\ndef event_recheck(self, event):")
        print(f"\nRecheck {self.find.selected_dir.get()}")
        self.find.reset()
        self.event_reset(event)
        self.after_idle(self.find.bn_find.invoke)

    def exit(self):
        self.find.exit()


class ADP(tk.Tk):
    """Class to run the ADPFind, ADPTable and ADPGallery GUIs."""

    def __init__(self, mode: str = "gallery", layout: str = "horizontal",
                 cfe: str = "process"):
        # 1. Check value of keywords
        if mode not in ["gallery", "table", "find"]:
            raise ValueError(f"mode={mode} is invalid. It's value must either "
                             f"be 'gallery', 'table' or 'find'.")
        if layout not in ["horizontal", "vertical"]:
            raise ValueError(f"layout={layout} is invalid. It's value must "
                             f"either be 'horizontal' or 'vertical'.")
        if cfe not in ["thread", "process"]:
            raise ValueError(f"cfe={cfe} is invalid. It's value must either "
                             f"be 'thread' or 'process'.")

        show_logo_in_terminal()

        # 2. Initialise and set up Tk window
        super().__init__()
        self["background"] = BG
        self.title('ANY DUPLICATED PHOTOS?')

        # 3. Sets the titlebar icon for the Tk window
        app_icon = str(CWD) + "/icons/app/ADP.png"
        wm_icon = ImageTk.PhotoImage(file=app_icon)
        wm_icon.image = app_icon
        self.tk.call('wm', 'iconphoto', self, wm_icon)

        # 4. Setup style of all ttk widgets
        self.ss = ttk.Style()
        customise_ttk_widgets_style(self.ss)

        # 5. Create the app widget
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        match mode:
            case "find":
                self.app = ADPFind(self, cfe="process")
            case "table":
                self.app = ADPTable(self, cfe="process", layout=layout)
            case "gallery":
                self.geometry('1300x600')
                self.app = ADPGallery(self, cfe=cfe, layout=layout)
        self.app.grid(row=0, column=0, sticky='nsew', padx=10, pady=(10, 0))

        # 6. Setup self window's shutdown
        self.protocol('WM_DELETE_WINDOW', self.exit)

        # 7. Start main events loop
        self.mainloop()

    def exit(self):
        """Function for shutting down root window"""
        mbox = messagebox.askokcancel("Quit",
                                      f"\nShut down ADP?\n",
                                      icon="question", default="ok")
        if mbox:
            print(f"\nExiting ADP...")
            self.app.exit()
            self.destroy()


def show_logo_in_terminal():
    print(
        f"        /AAAA           /DDDDDDDD       /PPPPPPPP   \n"
        f"      / AA _/AA        | DD     | DD   | PP_____/PP \n"
        f"     / AA   \ AA       | DD      | DD  | PP     | PP\n"
        f"    / AA     \ AA      | DD      | DD  | PP     | PP\n"
        f"   / AA AA AA AA AA    | DD      | DD  | PPPPPPPP/  \n"
        f"  / AA__________/ AA   | DD     | DD   | PP_____/   \n"
        f" / AA            \ AA  | DDDDDDDD /    | PP         \n"
        f" \/_/             \/_/ |/_______/      |/_/    ANY DUPLICATED PHOTOS?"
        )


def main():
    """Function run ADP GUI via commandline."""
    # 1. Set up the argument parser
    parser = argparse.ArgumentParser(
        description="GUI to find and delete duplicated photos quickly.")

    # 2. Define parser optional arguments
    mode = {"f": "find", "t": "table", "g": "gallery"}
    parser.add_argument("-m", "--mode",
                        type=str, default='g', choices=mode.keys(),
                        help="Run ADP in either 'f=find', 't=table' or "
                             "'g=gallery' mode.")
    layouts = {"h": "horizontal", "v": "vertical"}
    parser.add_argument("-l", "--layout",
                        type=str, choices=layouts.keys(),
                        help="Set GUI layout to be either 'h=horizontal', or "
                             "'v=vertical'.")
    cfe = {"p": "process", "t": "thread"}
    parser.add_argument("-c", "--cfe",
                        type=str, default='p', choices=cfe.keys(),
                        help="Set concurrent.future.Executor to either "
                             "'p=process' or 't=thread' type.")

    # 3. Get the submitted arguments
    args = parser.parse_args()

    # 4. Run GUI.
    match args.mode:
        case "f":
            ADP(mode=mode[args.mode], cfe=cfe[args.cfe])
        case "t":
            try:
                lay = layouts[args.layout]
            except KeyError as exc:
                if not exc.args[0]:
                    lay = "vertical"
                else:
                    raise KeyError(exc.args[0])
            finally:
                ADP(mode=mode[args.mode], layout=lay, cfe=cfe[args.cfe])
        case "g":
            try:
                lay = layouts[args.layout]
            except KeyError as exc:
                if not exc.args[0]:
                    lay = "horizontal"
                else:
                    raise KeyError(exc.args[0])
            finally:
                ADP(mode=mode[args.mode], layout=lay, cfe="thread")
                # Note: cfe="process" in gallery mode results in unstable
                #       performance. Consequently, cfe="thread" must be used
                #       in the meantime.


###############################################################################
# App SCRIPT TO CALL APPLICATION
###############################################################################
if __name__ == '__main__':
    # ADP(mode="find", cfe="process")  # stable
    # ADP(mode="table", layout="vertical", cfe="process")  # stable
    # ADP(mode="gallery", layout="horizontal", cfe="process")  # unstable: hangs randomly after several reruns
    ADP(mode="gallery", layout="horizontal", cfe="thread")  # stable but slower than cfe="process"
