# print(f"{__name__}")

# Python modules
import os
import threading
import queue
from time import perf_counter
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog

# External Packages
from PIL import Image, ImageTk

# Project modules
from adp.functions import timings
from adp.widgets.duplicates_db import DuplicatesDB
from adp.functions import (fast_scandir,
                           scandir_images_concurrently, )
from adp.functions.duplicates_finder_serial import detect_duplicates_serially
from adp.functions.duplicates_finder_concurrent import (
    detect_duplicates_concurrently)
from adp.widgets.constants import CWD, HOME, RING1, RING2, MSG0, BG
from adp.widgets.w_findindicators import DonutCharts, Findings
from adp.widgets.w_progressbar import Progressbarwithblank

__all__ = ["Find"]
__version__ = '0.1'
__author__ = 'Chia Yan Hon, Julian.'
__copyright__ = "Copyright 2024, Chia Yan Hon, Julian."
__license__ = "Apache License, Version 2.0"


class Find(ttk.Frame):
    """ A customised ttk widget to select a directory to find duplicated raster
    images within itself and it's sub-directories.

    Composition:
    It is a ttk.Frame widget that comprises 7 children widgets, namely:
    1. A "Folder" button to select a directory/folder that is to be searched
       for duplicated photos. All its sub-directories will also be searched.
    2. A "Find" button to first find all the photo files and second to find
       which of these photo files have duplicate(s). To expedite these
       find processes, a concurrent find photo algorithms and a
       serial/concurrent find duplicates algorithm are used.
    3. A Progressbarwithblank widget to animate the busy state of the cpu
       during the find processes.
    4. A Findings table to tabulate the Find results.
    5. Two donut charts to show the quantity and percentage of photos that are
       either unique or duplicates, and their respective byte sizes.
    6. Two DonutCharts widgets to show the quantity and percentage of duplicated
       photos that are either the original or copies, and their respective byte
       sizes.
    7. A label to show use-instructions and the selected directory path.

    Layout:
    This widget can be displayed in either a "horizontal" or "vertical" layout.

    Results:
    1. "Folder" button
       - self.selected_dir is a tk.StringVar storing the full path of the
                           selected directory.
    2. "Find" button
       - self.subfolders is a list of str objects of the full path of all
                         sub-directories.
       - self.rimages is a list of RasterImage instances.
       - self.duplicates is a dict of {hashhex: a set object with str objects
                         that define the full path of the found photo
                         duplicates}.
       - self.quantities is a tuple of integers defining the number of photos
                         that are duplicates, originals, and copies.

    Generated Virtual Events:
    "<<DirectorySelected>>" - generated after selecting directory.
    "<<FindDone>>"          - generated after detecting duplicated photos.
    """

    def __init__(self, master, **options):
        self.master = master
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
        try:
            cfe = options.pop("cfe")
        except KeyError:
            self.cfe = "process"  # default value
        else:
            if cfe in ["process", "thread"]:
                self.cfe = cfe  # concurrent.future.Executor
            else:
                raise ValueError(f"cfe={cfe} is invalid. It's value must "
                                 f"either be 'process' or 'thread'.")
        super().__init__(master, **options)

        # Initialise widget's icons variables
        i1 = Image.open(str(CWD) +
                        '/icons/franksouza183/Places-user-image-icon.png')
        i2 = Image.open(str(CWD) + '/icons/franksouza183/Actions-find-icon.png')
        self.icon_imgdir = ImageTk.PhotoImage(i1)
        self.icon_find = ImageTk.PhotoImage(i2)
        self.icon_imgdir.image = i1
        self.icon_find.image = i2

        # Initialise widget's variables
        self.selected_dir = tk.StringVar()  # updated by invoking Folder Button
        self.subfolders = None  # list of str objects
        self.rimages = []  # list of RasterImage instances
        self.duplicates = {}  # dict stores found duplicated photos
        self.quantities = None  # tuple(nduplicates, noriginals, ncopies)
        self._image_queue = queue.Queue()  # for moving stuff from thread to tk
        self._duplicates_queue = queue.Queue()  # for moving stuff from thread to tk
        self._find_queue = queue.Queue()  # for moving stuff from thread to tk

        self.bn_folder = None  # ttk.Button
        self.bn_find = None  # ttk.Button
        self.w_tab = None  # Custom widget
        self.w_pho = None  # Custom widget
        self.w_dup = None  # Custom widget
        self.w_pb = None  # Custom widget
        self.w_selected_path = None  # ttk.Label

        # Create sqlite database
        self.sqlite3_db = DuplicatesDB()
        self.sqlite3_db.create_table()

        # Create widgets inside self
        self._create_widgets()
        self._create_bindings()

    def _create_widgets(self):
        # Create Widgets
        self.bn_folder = ttk.Button(self, text='Folder', image=self.icon_imgdir,
                                    compound=tk.LEFT,
                                    command=self._select_directory)
        self.bn_find = ttk.Button(self, text='Find', image=self.icon_find,
                                  compound=tk.LEFT,
                                  command=self._start_find_duplicates_algorithm,
                                  )
        self.w_tab = Findings(self)
        self.w_pho = DonutCharts(self, title0="Photos", title1="Qty",
                                 title2="Size",
                                 legend1="Unique", legend2="Duplicates",
                                 **RING1)
        self.w_dup = DonutCharts(self, title0="Duplicates", title1="Qty",
                                 title2="Size",
                                 legend1="Original", legend2="Copies",
                                 **RING2)
        self.reset()
        self.disable_find_button()
        self.w_selected_path = ttk.Label(self, justify="left",
                                         style='Bold.TLabel',
                                         textvariable=self.selected_dir)
        self.selected_dir.set(MSG0)
        self.w_pb = Progressbarwithblank(self, orient=tk.VERTICAL,
                                         mode='indeterminate')
        self.w_pb.blank["style"] = "Blank.TLabel"

        # Grid Widgets
        self.bn_folder.grid(row=0, column=0, sticky='nw')
        self.bn_find.grid(row=1, column=0, sticky='nw')
        self.w_pb.grid_pb(row=0, column=1, rowspan=2, sticky='nsw', padx=(5, 0))
        self.w_tab.grid(row=0, column=2, rowspan=2, sticky='nw', padx=(5, 0))
        if self.layout in "horizontal":
            self.w_pho.grid(row=0, column=3, rowspan=2, sticky='nw',
                            padx=(20, 0))
            self.w_dup.grid(row=0, column=4, rowspan=2, sticky='nw',
                            padx=(20, 0))
            self.w_selected_path.grid(row=2, column=0, columnspan=4,
                                      sticky="nw")
        elif self.layout in "vertical":
            self.w_selected_path.grid(row=2, column=0, columnspan=4,
                                      sticky='nw')
            self.w_pho.grid(row=3, column=0, columnspan=4, sticky='nw',
                            pady=(10, 0))
            self.w_dup.grid(row=4, column=0, columnspan=4, sticky='nw',
                            pady=(10, 0))
            self.columnconfigure(3, weight=1)

        self.w_pb.hide()

    def _create_bindings(self):
        self.bind("<<DirectorySelected>>", self._event_enable_bn_find)
        self.bind("<<FindDone>>", self._event_populate_sqlite_db)

    # --------- Event Handlers --------- #
    def _event_enable_bn_find(self, event):
        # print(f"\ndef _event_enable_bn_find(self, event):")
        self.bn_find.instate(["disabled"], self.enable_find_button)

    def _event_disable_bn_find(self, event):
        # print(f"\ndef _event_disable_bn_find(self, event):")
        self.bn_find.instate(["!disabled"], self.disable_find_button)


    def _event_populate_sqlite_db(self, event):
        r0 = perf_counter()
        self.sqlite3_db.populate(self.selected_dir.get(), self.duplicates)
        r1 = perf_counter()
        loadtime = r1 - r0
        tl, tl_units = timings(loadtime)
        print(f'SQLite3 database created in {tl:.6f} {tl_units}.')
        self.event_generate("<<Sqlite3DBPopulated>>", when="tail")
        # print(f'<<Sqlite3DBPopulated>> generated by {self}')

    # --------- Methods ---------#
    def show_selected_path(self):
        self.w_selected_path.grid()

    def hide_selected_path(self):
        self.w_selected_path.grid_remove()

    def disable_buttons(self):
        self.disable_folder_button()
        self.disable_find_button()

    def disable_find_button(self):
        self.bn_find.state(['disabled'])

    def disable_folder_button(self):
        self.bn_folder.state(['disabled'])

    def enable_buttons(self):
        self.enable_folder_button()
        self.enable_find_button()

    def enable_find_button(self):
        self.bn_find.state(['!disabled'])

    def enable_folder_button(self):
        self.bn_folder.state(['!disabled'])

    def reset(self):
        # 1. Reset widgets
        self.w_tab.reset()
        self.w_pho.reset()
        self.w_dup.reset()
        # Reset attributes
        if self.rimages:
            self.rimages.clear()
        if self.duplicates:
            self.duplicates.clear()
        if self.quantities:
            self.quantities = None
        if not self.sqlite3_db.is_table_empty():
            self.sqlite3_db.reset_table()

    def exit(self):
        self.reset()
        self.sqlite3_db.close()

    # --------- Callbacks ---------#
    def _select_directory(self):
        """Callback to configure tk.filedialog.askdirectory widget behaviour and
        to set the value of the control variable self.selected_dir which defines
        the path that is to be scanned. Activated by ttk.Button self.bn_folder.
        """
        # print(f"\ndef _select_directory(self):")

        old = self.selected_dir.get()
        if old in MSG0:
            initialdir = HOME
        else:
            initialdir = old
        new = tk.filedialog.askdirectory(
            initialdir=initialdir,
            title="Select The Folder That Is To Be Scanned."
        )
        # print(f"{new=} {type(new)=}")
        # Note: For askdirectory(), when the Cancel button is pressed as its
        # 1st event, new will have a value of an empty tuple (i.e. new=()).
        # Subsequent triggering of the Cancel button will return new with a
        # value of an empty str (i.e. new="" or new=''). The pythonic way to
        # check that these types are empty (i.e. these objects don't contain
        # any objects) is to use "not".
        if not new:
            return None  # Don't change self.selected_dir
        else:
            # Use the selected directory and reset all attributes of this class.
            self.selected_dir.set(new)
            print(f'\n{self.selected_dir.get()}')
            self.reset()
            # Generate virtual event <<DirectorySelected>>
            # print(f'<<DirectorySelected>> generated')
            self.event_generate("<<DirectorySelected>>", when="tail")

    def _start_find_duplicates_algorithm(self):
        """Callback to recursively scan self.selected_dir and its subdirectories
        for photo duplicates. A concurrent-process algorithm is used to quickly
        search for raster images. Their duplicates are then detected either
        serially or concurrently depending on conditions. The concurrent
        algorithm to find raster images is many times faster than a serial
        approach. Invoked after clicking self.bn_find.
        """
        # print(f"\ndef _start_find_duplicates_algorithm(self):")
        # 1. Get path
        folder = self.selected_dir.get()
        # print(f"{type(folder)=} {folder=}")

        # 2. Run progress bar and find photos plus detect duplicates using
        # two different threads.
        if not folder:
            return  # Do nothing when self.selected_dir does not have a path
        elif folder in MSG0:
            return  # Do nothing

        # 3. Update widgets appearances
        self.disable_buttons()
        self.w_pb.show()
        self.w_pb.start(10)

        # 4. Find all subfolders within folder recursively & update self.w_tab
        start0 = perf_counter()
        subfolders = fast_scandir(folder)
        end0 = perf_counter()
        nsubfolders = len(subfolders)
        time_subfolders = end0 - start0
        tsf, tsf_units = timings(time_subfolders)
        self.w_tab.update_subfolders(nsubfolders, tsf, tsf_units)
        print(f"Found {nsubfolders} subfolders in {time_subfolders:.6f} secs.")

        # 5. Find photos within folder and its subfolders & update self.w_tab
        start1 = perf_counter()
        folders = [folder] + subfolders
        findthread = threading.Thread(target=self._find_raster_images_in,
                                      args=(folders,), name="findthread")
        findthread.start()
        self._check_thread(findthread, start0)

    def _find_raster_images_in(self, folders):
        """Find raster images in folder and its subfolders"""
        # print(f"\ndef _find_raster_images_in(self, folders):")
        start = perf_counter()
        rimages = scandir_images_concurrently(folders, cfe=self.cfe)
        # print(f"{rimages=}")
        end = perf_counter()
        self._find_queue.put(("rimages", rimages))
        time_findphotos = end - start
        nphotos = len(rimages)
        tp, tp_units = timings(time_findphotos)
        self._find_queue.put(("nphotos", nphotos, tp, tp_units))
        print(f'Found {nphotos} photos in {time_findphotos:.6f} secs.')

    def _check_thread(self, thread, start0):
        # print(f"\ndef _check_thread(self, thread, start0):")
        duration = 100
        try:
            info = self._find_queue.get(block=False)
        except queue.Empty:
            # let's try again later
            self.after(duration, lambda: self._check_thread(thread, start0))
        else:
            # print(f"self._check_thread got, {info=}")
            # Extract info from queue
            match info[0]:
                case "rimages":
                    self.rimages = info[1]
                    self.after(duration, lambda: self._check_thread(thread,
                                                                    start0))
                case "nphotos":
                    self.w_tab.update_photos(*info[1:])
                    self._dupthread(start0)

    def _dupthread(self, start0):
        dupthread = threading.Thread(target=self._detect_duplicates,
                                     args=(start0,), name="dupthread")
        dupthread.start()
        self._check_duplicates_queue(start0, dupthread)

    def _detect_duplicates(self, start0):
        """Detect duplicated photos in self.rimage & update self.w_tab"""
        # print(f"\ndef _detect_duplicates(self, start0):")
        # print(f"{threading.main_thread()=} {threading.current_thread()=}")
        dup_queue = self._duplicates_queue
        start2 = perf_counter()
        if len(self.rimages) <= 1000:
            duplicates = detect_duplicates_serially(self.rimages)
        else:
            try:
                duplicates = detect_duplicates_concurrently(self.rimages,
                                                            cfe=self.cfe)
            except ValueError:
                duplicates = detect_duplicates_serially(self.rimages)
        end2 = perf_counter()
        dup_queue.put(("duplicates", duplicates))

        noriginals = len(duplicates)
        ncopies = sum([len(i) - 1 for i in duplicates.values()])
        nduplicates = noriginals + ncopies
        quantities = (nduplicates, noriginals, ncopies)
        time_findduplicates = end2 - start2
        time_total = end2 - start0
        td, td_units = timings(time_findduplicates)
        tt, tt_units = timings(time_total)
        dup_queue.put(("nduplicates", nduplicates, td, td_units))
        dup_queue.put(("quantities", quantities))
        dup_queue.put(("ntotal", tt, tt_units))
        print(f'Found {nduplicates} duplicated photos in'
              f' {time_findduplicates:.6f} secs with ({noriginals}'
              f' originals & {ncopies} copies).\n'
              f'Total time is {time_total:.6f} secs.')

        # Calculate Size (Bytes) of Duplicates
        size_o = sum([os.stat(j).st_size for i in
                      duplicates.values() for j in list(i)[:1]])
        size_c = sum([os.stat(j).st_size for i in
                      duplicates.values() for j in list(i)[:-1]])
        # Calculate Size (Bytes) of Photos
        size_p = sum((i.size for i in self.rimages))
        size_d = size_o + size_c
        size_u = size_p - size_d
        # print(f"{size_p=} {size_d=} {size_u=}")
        # Calculate quantity of non-duplicated photos in self.rimages
        nphotos = len(self.rimages)
        nunique = nphotos - nduplicates
        # print(f"{nunique=}")
        dup_queue.put(("w_pho", nunique, nduplicates, size_u, size_d))
        dup_queue.put(("w_dup", noriginals, ncopies, size_o, size_c))

    def _check_duplicates_queue(self, start0, dthread):
        # print(f"\ndef _check_duplicates_queue(self, start0):")
        duration = 100
        try:
            info = self._duplicates_queue.get(block=False)
        except queue.Empty:
            # let's try again later
            self.after(duration, lambda: self._check_duplicates_queue(start0,
                                                                      dthread))
        else:
            # print(f"self._check_duplicates_queue got, {info=}")
            # print(f"{dthread.name}.is_alive()={dthread.is_alive()}"
            #       f" {threading.main_thread()=} {threading.current_thread()=}")
            match info[0]:
                case "nduplicates":
                    self.w_tab.update_duplicates(*info[1:])
                    self.after(duration,
                               lambda: self._check_duplicates_queue(start0,
                                                                    dthread))
                case "duplicates":
                    self.duplicates = info[1]
                    # print(f"{self.duplicates=}")
                    self.after(duration,
                               lambda: self._check_duplicates_queue(start0,
                                                                    dthread))
                case "quantities":
                    self.quantities = info[1]
                    self.after(duration,
                               lambda: self._check_duplicates_queue(start0,
                                                                    dthread))
                case "ntotal":
                    self.w_tab.update_total(*info[1:])
                    self.after(duration,
                               lambda: self._check_duplicates_queue(start0,
                                                                    dthread))
                case "w_pho":
                    self.w_pho.update_gui(*info[1:])
                    self.after(duration,
                               lambda: self._check_duplicates_queue(start0,
                                                                    dthread))
                case "w_dup":
                    self.w_dup.update_gui(*info[1:])
                    self.w_pb.stop()
                    self.w_pb.hide()
                    self.enable_folder_button()
                    # print(f'<<FindDone>> generated by {self}')
                    self.after_idle(self.event_generate, "<<FindDone>>")


if __name__ == '__main__':
    from adp.widgets import w_ttkstyle
    import tkinter.messagebox as messagebox

    root = tk.Tk()
    root.title('ANY DUPLICATED PHOTOS?')
    root["background"] = BG
    s = ttk.Style()
    # Initialise customised widgets styles
    w_ttkstyle.customise_ttk_widgets_style(s)
    # app = Find(root, layout="row")
    app = Find(root, layout="vertical", cfe="process")
    app.grid(row=0, column=0, sticky='nsew', padx=10, pady=(10, 0))
    root.rowconfigure(0, weight=1)  # stretch vertically
    # root.rowconfigure(1, weight=1)  # stretch vertically
    root.columnconfigure(0, weight=1)  # stretch horizontally

    def exit_root():
        """Function for shutting down root window"""
        mbox = messagebox.askokcancel("Quit",
                                      f"\nShut down ADP?\n",
                                      icon="question", default="ok")
        if mbox:
            print(f"\nExiting Application...")
            app.exit()
            root.destroy()

    # Setup root window's shutdown
    root.protocol('WM_DELETE_WINDOW', exit_root)

    # Start app in main events loop
    root.mainloop()
