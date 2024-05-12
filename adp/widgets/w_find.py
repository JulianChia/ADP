# Python modules
import os
import threading
import queue
import signal
from time import perf_counter

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog


# External Packages
from PIL import Image, ImageTk

# Project modules
from adp.functions.tools import timings, pop_kwargs
from adp.functions.picture_finder_concurrent_one_folder import get_rasterimages_in_one_folder_concurrently
from adp.functions.picture_finder_concurrent import (fast_scandir, scandir_images_concurrently)
from adp.functions.duplicates_finder_serial import detect_duplicates_serially
from adp.functions.duplicates_finder_concurrent import (detect_duplicates_concurrently)
from adp.widgets.constants import CWD, HOME, RING1, RING2, MSG0, BG
from adp.widgets.duplicates_db import DuplicatesDB
from adp.widgets.w_findindicators import DonutCharts, Findings
from adp.widgets.w_progressbar import Progressbarwithblank

__all__ = ["Find"]
__version__ = '0.1'
__license__ = "Apache License, Version 2.0"
__copyright__ = "Copyright 2024, Chia Yan Hon, Julian."
__author__ = 'Chia Yan Hon, Julian.'
__email__ = "julianchiayh@gmail.com"


class Find(ttk.Frame):
    """ A customised ttk widget to select a directory to find duplicated raster
    images within itself and it's sub-directories.

    Composition:
    It is a ttk.Frame widget that comprises 7 children widgets, namely:
    1. A "Folder" button to select a directory/folder that is to be searched
       for duplicated pictures. All its sub-directories will also be searched.
    2. A "Find" button to first find all the picture files and second to find
       which of these picture files have duplicate(s). To expedite these
       find processes, a concurrent find picture algorithms and a
       serial/concurrent find duplicates algorithm are used.
    3. A Progressbarwithblank widget to animate the busy state of the cpu
       during the find processes.
    4. A Findings table to tabulate the Find results.
    5. Two donut charts to show the quantity and percentage of pictures that are
       either unique or duplicates, and their respective byte sizes.
    6. Two DonutCharts widgets to show the quantity and percentage of duplicated
       pictures that are either the original or copies, and their respective byte
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
                         that define the full path of the found picture
                         duplicates}.
       - self.quantities is a tuple of integers defining the number of pictures
                         that are duplicates, originals, and copies.

    Generated Virtual Events:
    "<<DirectorySelected>>" - generated after selecting directory.
    "<<FindDone>>"          - generated after detecting duplicated pictures.

    icons source:
    <img src="https://icons.iconarchive.com/icons/franksouza183/fs/48/Places-user-image-icon.png" width="48" height="48">
    <img src="https://icons.iconarchive.com/icons/franksouza183/fs/48/Actions-find-icon.png" width="48" height="48">
    """

    def __init__(self, master, gallery=False, **options) -> None:
        self.master = master
        self._gallery = gallery
        self._cfe = pop_kwargs("cfe", ["process", "thread"], options)
        self._layout = pop_kwargs("layout", ["vertical", "horizontal"], options)
        super().__init__(master, **options)

        # Initialise icons attributes
        i1 = Image.open(str(CWD) + '/icons/Places-user-image-icon.png')
        i2 = Image.open(str(CWD) + '/icons/Actions-find-icon.png')
        self._icon_imgdir = ImageTk.PhotoImage(i1)
        self._icon_find = ImageTk.PhotoImage(i2)
        self._icon_imgdir.image = i1
        self._icon_find.image = i2

        # Initialise public attributes
        self.selected_dir = tk.StringVar()  # updated by invoking Folder Button
        self.subfolders = None  # list of str objects
        self.rimages = []  # list of RasterImage instances
        self.duplicates = {}  # dict stores found duplicated pictures
        self.quantities = None  # tuple(nduplicates, noriginals, ncopies)

        # Initialise Find process attributes
        self._findthread = None  # threading.Thread object
        self._dupthread = None  # threading.Thread object
        self._findqueue = queue.Queue()  # for moving stuff from threads to tkinter during the Find process
        self._exitevent = threading.Event()  # for graceful exit
        self._start0 = None

        # Initialise children widgets attributes
        self.bn_folder = None  # ttk.Button
        self.bn_find = None  # ttk.Button
        self.w_tab = None  # Custom widget
        self.w_pho = None  # Custom widget
        self.w_dup = None  # Custom widget
        self.w_pb = None  # Custom widget
        self.w_selected_path = None  # ttk.Label
        self._progress = tk.DoubleVar()
        self._progress.set(0.0)

        # Create sqlite database
        self.sqlite3_db = DuplicatesDB()
        self.sqlite3_db.create_table()

        # Create widgets inside self
        self._create_widgets()
        self._create_bindings()

        # Define handling of SIGTERM
        signal.signal(signal.SIGTERM, self._exit_signal_handler)

    def _exit_signal_handler(self, signal_number, frame):
        print(f'Received Signal {signal_number} {frame}')
        self._exitevent.set()

    def _create_widgets(self) -> None:
        # Create Widgets
        self.bn_folder = ttk.Button(self, text='Folder',
                                    image=self._icon_imgdir,
                                    compound=tk.LEFT,
                                    command=self._select_directory)
        self.bn_find = ttk.Button(self, text='Find',
                                  image=self._icon_find,
                                  compound=tk.LEFT,
                                  command=self._start_find_duplicates_algorithm,
                                  )
        self.w_tab = Findings(self)
        self.w_pho = DonutCharts(self, title0="Pictures", title1="Qty",
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
                                         mode='determinate',
                                         variable=self._progress,
                                         maximum=1.0, second=True)
        self.w_pb.blank["style"] = "Blank.TLabel"
        self.w_pb.hide_pb2()

        # Grid Widgets
        self.bn_folder.grid(row=0, column=0, sticky='nw', pady=(0, 5))
        self.bn_find.grid(row=1, column=0, sticky='nw')
        self.w_pb.grid_pb(row=0, column=1, rowspan=2,  sticky='nsw',
                          padx=(5, 0))
        self.w_tab.grid(row=0, column=2, rowspan=2, sticky='nw', padx=(5, 0))
        if self._layout in "horizontal":
            self.w_pho.grid(row=0, column=3, rowspan=2, sticky='nw',
                            padx=(20, 0))
            self.w_dup.grid(row=0, column=4, rowspan=2, sticky='nw',
                            padx=(20, 0))
            self.w_selected_path.grid(row=2, column=0, columnspan=4,
                                      sticky="nw")
        elif self._layout in "vertical":
            self.w_selected_path.grid(row=2, column=0, columnspan=4,
                                      sticky='nw')
            self.w_pho.grid(row=3, column=0, columnspan=4, sticky='nw',
                            pady=(10, 0))
            self.w_dup.grid(row=4, column=0, columnspan=4, sticky='nw',
                            pady=(10, 0))
            self.columnconfigure(3, weight=1)

        self.w_pb.hide()

    def _create_bindings(self) -> None:
        self.bind("<<DirectorySelected>>", self._event_enable_bn_find)
        self.bind("<<FindDone>>", self._event_populate_sqlite_db)

    # --------- Event Handlers --------- #
    def _event_enable_bn_find(self, event) -> None:
        # print(f"\ndef _event_enable_bn_find(self, event):")
        self.bn_find.instate(["disabled"], self.enable_find_button)

    def _event_disable_bn_find(self, event) -> None:
        # print(f"\ndef _event_disable_bn_find(self, event):")
        self.bn_find.instate(["!disabled"], self.disable_find_button)

    def _event_populate_sqlite_db(self, event) -> None:
        r0 = perf_counter()
        self.sqlite3_db.populate(self.selected_dir.get(), self.duplicates)
        r1 = perf_counter()
        loadtime = r1 - r0
        tl, tl_units = timings(loadtime)
        print(f'SQLite3 database created in {tl:.6f} {tl_units}.')
        self.event_generate("<<Sqlite3DBPopulated>>", when="tail")
        # print(f'<<Sqlite3DBPopulated>> generated by {self}')

    # --------- Methods ---------#
    def show_selected_path(self) -> None:
        self.w_selected_path.grid()

    def hide_selected_path(self) -> None:
        self.w_selected_path.grid_remove()

    def disable_buttons(self) -> None:
        self.disable_folder_button()
        self.disable_find_button()

    def disable_find_button(self) -> None:
        self.bn_find.state(['disabled'])

    def disable_folder_button(self) -> None:
        self.bn_folder.state(['disabled'])

    def enable_buttons(self) -> None:
        self.enable_folder_button()
        self.enable_find_button()

    def enable_find_button(self) -> None:
        self.bn_find.state(['!disabled'])

    def enable_folder_button(self) -> None:
        self.bn_folder.state(['!disabled'])

    def reset(self) -> None:
        # 1. Reset widgets
        self.w_tab.reset()
        self.w_pho.reset()
        self.w_dup.reset()
        self._progress.set(0.0)
        # 2. Reset attributes
        if self.rimages:
            self.rimages.clear()
        if self.duplicates:
            self.duplicates.clear()
        if self.quantities:
            self.quantities = None
        if not self.sqlite3_db.is_table_empty():
            self.sqlite3_db.reset_table()
        del self._findthread
        del self._dupthread
        self._findthread = None
        self._dupthread = None

    def exit(self) -> None:
        self._exitevent.set()
        self.reset()
        self.sqlite3_db.close()

    # --------- Callbacks ---------#
    def _select_directory(self) -> None:
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
            text = f"\n{self.selected_dir.get()}"
            print(text)
            self.reset()
            # Generate virtual event <<DirectorySelected>>
            # print(f'<<DirectorySelected>> generated')
            self.event_generate("<<DirectorySelected>>", when="tail")

    def _start_find_duplicates_algorithm(self) -> None:
        """Callback to recursively scan self.selected_dir and its subdirectories
        for picture duplicates. A concurrent-process algorithm is used to
        quickly search for raster images. Their duplicates are then detected
        either serially or concurrently depending on conditions. The concurrent
        algorithm to find raster images is many times faster than a serial
        approach. Invoked after clicking self.bn_find.
        """
        # 1. Get path
        folder = self.selected_dir.get()

        # 2. Run progress bar and find pictures plus detect duplicates using
        # two different threads.
        if not folder:
            return  # Do nothing when self.selected_dir does not have a path
        elif folder in MSG0:
            return  # Do nothing

        # 3. Update widgets appearances
        self.disable_buttons()
        self.w_pb.show()

        # 4. Find all subfolders within folder recursively & update self.w_tab
        self._start0 = perf_counter()
        self.subfolders = fast_scandir(folder)
        end0 = perf_counter()
        nsubfolders = len(self.subfolders)
        time_subfolders = end0 - self._start0
        tsf, tsf_units = timings(time_subfolders)
        self.w_tab.update_subfolders(nsubfolders, tsf, tsf_units)
        text = f"Subfolders: Found {nsubfolders} in {time_subfolders:.6f} secs."
        print(text)

        # 5. Find pictures within folder and its subfolders & update self.w_tab
        if self._gallery and self._cfe in "process":
            self.update()  # for better stability

        self._check_find_queue()
        if nsubfolders == 0:
            self.after(100,
                       self._start_concurrent_picture_detection_for_one_folder)
        else:
            self.after(100,
                       self._start_concurrent_picture_detection_for_many_folders)

    def _detect_duplicates(self) -> None:
        """Detect duplicated pictures in self.rimage"""
        if len(self.rimages) <= 1000:
            self.after(100,
                       self._start_serial_duplicates_detection)
        else:
            try:
                self.after(100,
                           self._start_concurrent_pool_duplicates_detection)
            except ValueError:
                self.after(100,
                           self._start_serial_duplicates_detection)

    def _start_concurrent_picture_detection_for_one_folder(self) -> None:
        self._findthread = threading.Thread(
            target=get_rasterimages_in_one_folder_concurrently,
            args=(self.selected_dir.get(), self._findqueue),
            kwargs={"ncpu": os.cpu_count(),
                    "cfe": self._cfe,
                    "exit_event": self._exitevent},
            name="findthread",)
        self._findthread.start()

    def _start_concurrent_picture_detection_for_many_folders(self) -> None:
        folders = [self.selected_dir.get()] + self.subfolders
        self._findthread = threading.Thread(
            target=scandir_images_concurrently,
            args=(folders, self._findqueue),
            kwargs={"ncpu": os.cpu_count(),
                    "cfe": self._cfe,
                    "exit_event": self._exitevent},
            name="findthread",)
        self._findthread.start()

    def _start_serial_duplicates_detection(self) -> None:
        self._dupthread = threading.Thread(
            target=detect_duplicates_serially,
            args=(self.rimages, self._findqueue),
            name="dupthread",)
        self._dupthread.start()

    def _start_concurrent_pool_duplicates_detection(self) -> None:
        self._dupthread = threading.Thread(
            target=detect_duplicates_concurrently,
            args=(self.rimages, self._findqueue),
            kwargs={"ncpu": os.cpu_count(),
                    "cfe": self._cfe,
                    "exit_event": self._exitevent},
            name="dupthread",)
        self._dupthread.start()

    def _check_find_queue(self) -> None:
        duration = 1
        try:
            # Extract info from queue
            info = self._findqueue.get(block=False)
        except queue.Empty:
            self.after(duration, lambda: self._check_find_queue())
        else:
            # print(f"self._check_find_queue got, {info=}")
            # Proces info
            match info[0]:
                case "FindRunning":
                    jobs_completed, njobs = info[1:]
                    self._progress.set(jobs_completed/njobs)
                    self.after(duration, lambda: self._check_find_queue())
                case "FindCompleted":
                    self.rimages, start1, end1 = info[1:]
                    time_findpictures = end1 - start1
                    npictures = len(self.rimages)
                    tp, tp_units = timings(time_findpictures)
                    self.w_tab.update_pictures(npictures, tp, tp_units)
                    text = (f'\n{"Found":>17} {npictures} in'
                            f' {time_findpictures:.6f} secs.')
                    print(text)
                    if self.rimages:
                        self._progress.set(0.0)
                        self._detect_duplicates()
                    else:
                        total_time = end1-self._start0
                        text = (f'Duplicates: Found 0.\n'
                                f'Total time: {total_time:.6f} secs.')
                        print(text)
                        self.w_tab.update_duplicates(0, 0.0, "secs")
                        self.w_tab.update_total(tp, tp_units)
                        self.w_pho.update_gui(0, 0, 0.0, 0.0)
                        self.w_dup.update_gui(0, 0, 0.0, 0.0)
                        self.w_pb.hide()
                        self.enable_folder_button()
                        self.after_idle(self.event_generate, "<<FindDone>>")
                    self.after(duration, lambda: self._check_find_queue())
                case "DupRunning":
                    jobs_completed, njobs = info[1:]
                    self._progress.set(jobs_completed / njobs)
                    self.after(duration, lambda: self._check_find_queue())
                case "DupCompleted":
                    duplicates, start2, end2 = info[1:]
                    self.duplicates = duplicates
                    noriginals = len(duplicates)
                    ncopies = sum([len(i) - 1 for i in duplicates.values()])
                    nduplicates = noriginals + ncopies
                    self.quantities = (nduplicates, noriginals, ncopies)
                    time_findduplicates = end2 - start2
                    time_total = end2 - self._start0
                    td, td_units = timings(time_findduplicates)
                    tt, tt_units = timings(time_total)
                    self.w_tab.update_duplicates(nduplicates, td, td_units)
                    self.w_tab.update_total(tt, tt_units)
                    text = (f'\n{"Found":>17} {nduplicates} in'
                            f' {time_findduplicates:.6f} secs:'
                            f' {noriginals} originals & {ncopies} copies.\n'
                            f'Total time: {time_total:.6f} secs.')
                    print(f"{text}")
                    # Calculate Size (Bytes) of Duplicates
                    size_o = sum([os.stat(j).st_size for i in
                                  duplicates.values() for j in list(i)[:1]])
                    size_c = sum([os.stat(j).st_size for i in
                                  duplicates.values() for j in list(i)[:-1]])
                    # Calculate Size (Bytes) of Pictures
                    size_p = sum((i.size for i in self.rimages))
                    size_d = size_o + size_c
                    size_u = size_p - size_d
                    # Calculate quantity of non-duplicated pictures in
                    # self.rimages
                    npictures = len(self.rimages)
                    nunique = npictures - nduplicates
                    self.w_pho.update_gui(nunique, nduplicates, size_u, size_d)
                    self.w_dup.update_gui(noriginals, ncopies, size_o, size_c)
                    self.w_pb.hide()
                    self.enable_folder_button()
                    self.after_idle(self.event_generate, "<<FindDone>>")


if __name__ == '__main__':
    from adp.widgets import w_ttkstyle
    import tkinter.messagebox as messagebox

    root = tk.Tk()
    root.title('ANY DUPLICATED PICTURES?')
    root["background"] = BG
    s = ttk.Style()
    # Initialise customised widgets styles
    w_ttkstyle.customise_ttk_widgets_style(s)
    find = Find(root)                         # cfe="process", layout="vertical"
    # find = Find(root, cfe="thread")         # cfe="thread",  layout="vertical"
    # find = Find(root, layout="horizontal")  # cfe="process", layout="horizontal"
    find.grid(row=0, column=0, sticky='nsew', padx=10, pady=(10, 0))
    root.rowconfigure(0, weight=1)  # stretch vertically
    root.columnconfigure(0, weight=1)  # stretch horizontally

    # def exit_gracefully(signal_number, frame):
    #     print(f'Received Signal {signal_number} {frame}')
    #     sys.exit(0)
    #
    # def exit_immediately(signal_number, frame):
    #     print(f'Received Signal {signal_number} {frame}')
    #     os.kill(os.getppid(), signal.SIGKILL)
    #
    # signal.signal(signal.SIGTERM, exit_gracefully)
    # signal.signal(signal.SIGINT, exit_immediately)

    def exit_root():
        """Function for shutting down root window"""
        mbox = messagebox.askokcancel("Quit",
                                      f"\nShut down ADP?\n",
                                      icon="question", default="ok")
        if mbox:
            print(f"\nExiting Application...")
            find.exit()
            root.quit()
            root.destroy()

    # Setup root window's shutdown
    root.protocol('WM_DELETE_WINDOW', exit_root)

    # Start app in main events loop
    root.mainloop()
