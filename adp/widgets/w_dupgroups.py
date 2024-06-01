# Python modules
import tkinter as tk
import tkinter.ttk as ttk
from pathlib import Path
import concurrent.futures as cf
import queue
import os
import threading
from itertools import repeat

# External Packages
from PIL import Image, ImageTk

# Project module
from adp.functions import filesize

__all__ = ["DupGroup", "get_thumbnail", "get_thumbnail_c",
           "get_thumbnails_concurrently_with_queue", ]
__version__ = '0.1.1'
__license__ = "Apache License, Version 2.0"
__copyright__ = "Copyright 2024, Chia Yan Hon, Julian."
__author__ = 'Chia Yan Hon, Julian.'
__email__ = "julianchiayh@gmail.com"


def get_thumbnail(fpath: str, psize: tuple[int, int] = (200, 200)) -> Image:
    """Function uses the Image module of the Pillow pkg to convert a picture to
    a thumbnail size picture and returns the thumbnail picture.

    fpath - file full path
    psize - desired pixel width and height of thumbnail,
    """
    # print(f"{threading.main_thread()=} {threading.current_thread()=}")
    with Image.open(fpath) as img:
        img.load()
    img.thumbnail(psize, resample=Image.Resampling.NEAREST, reducing_gap=1.1)
    # Above options used to gain optimal conversion performance at the
    # expense of quality.
    return img


def get_thumbnail_c(giid: str, fiid: str, fpath: str,
                    psize: tuple[int, int] = (200, 200)) \
        -> tuple[str, str, Image]:
    """Function uses the Image module of the Pillow pkg to convert a picture to
    a thumbnail size picture and returns the thumbnail picture along with it's
    giid and fiid which are arguments of this function.

    giid - group item id for a tkinter.ttk.Treeview widget
    fiid - file item id for a tkinter.ttk.Treeview widget
    fpath - file full path
    psize - desired pixel width and height of thumbnail,
    """
    # print(f"{threading.main_thread()=} {threading.current_thread()=}")
    with Image.open(fpath) as img:
        img.load()
    img.thumbnail(psize, resample=Image.Resampling.NEAREST, reducing_gap=1.1)
    # Above options used to gain optimal conversion performance at the
    # expense of quality.
    return giid, fiid, img


def get_thumbnails_concurrently_with_queue(
        g_iids: list, f_iids: list, f_paths: list, rqueue: queue.Queue,
        ncpu : int = os.cpu_count(),
        cfe: str = "Process",
        exit_event: threading.Event = None,) -> None:
    """Function to concurrently convert a list of picture files to
    thumbnail-sized pictures(tsp). These tsps can then be extracted from
    `rqueue` individually."""
    job_fn = get_thumbnail_c
    match cfe:
        case "process": executor = cf.ProcessPoolExecutor(max_workers=ncpu)
        case "thread": executor = cf.ThreadPoolExecutor(max_workers=ncpu)
    with executor as execu:
        for giid, fiids, fpaths in zip(g_iids, f_iids, f_paths):
            job_iters = repeat(giid, len(fiids)), fiids, fpaths,
            results = execu.map(job_fn, *job_iters)
            for result in results:
                # Emergency exit
                if isinstance(exit_event, threading.Event):
                    if exit_event.is_set():
                        break
                # Put result in queue
                rqueue.put(("thumbnail", result))
    # Inform mainthread that job has completed
    rqueue.put(("completed", ()))


class DupGroup(ttk.Frame):
    """A customised ttk.Frame widget to show the thumbnails of duplicated
    pictures.

    Construction:
        It consists of 2 children ttk.Frame widgets gridded side-by-side:
        (1) Right ttk.frames (i.e. self.imagesframe):
            - consist of ttk.Checkbuttons that display the thumbnails and
              file item ID (i.e. fiid) of the duplicate pictures. Their left to
              right ordering sequence denotes the oldest picture (i.e. original)
               to the latest pictures (i.e. copies).
        (2) Left ttk.frames (i.e. self.infoframe):
            - consists of ttk.Labels that displays the group item id (giid),
              quantity and the total size of duplicate pictures.

     User Method:
     .reset() - to destroy/clear all its contents.
     """

    def __init__(self, master, g_iid: str, f_iids: list, f_paths: list,
                 f_selected: list, with_image=True, **options):
        super().__init__(master, style='DupGroup.TFrame', **options)
        self.master = master
        self.g_iid = g_iid
        self.f_iids = f_iids
        self.f_paths = f_paths
        self.f_selected = f_selected
        self.total_size = self.get_total_size()

        self.infoframe = None  # A ttk.Frame widget
        self.imagesframe = None  # A ttk.Frame widget

        self.iff_lbgrp = None  # A ttk.Frame widget
        self.iff_lbnimages = None  # A ttk.Frame widget
        self.iff_lbsize = None  # A ttk.Frame widget

        self.imf_thumbnails = {}  # {fiid: ImageTk.PhotoImage, ...}
        self.imf_checkvalues = {}  # {fiid: tk.IntVar, ...}
        self.imf_checkbuttons = {}  # {fiid: ttk.Checkbutton, ...}

        self._create_widgets_inside_self()
        if with_image:
            self._create_checkbuttons()
        else:
            self._create_checkbuttons(with_image=False)
        self._create_stats()
        self._update_stats()
        # self.bind("<Configure>", lambda _: self.update_idletasks())

    def _create_widgets_inside_self(self):
        self.imagesframe = ttk.Frame(self, style='infoframe.TFrame',
                                     relief=tk.FLAT)
        self.infoframe = ttk.Frame(self, style='infoframe.TFrame',
                                   relief=tk.FLAT)
        self.imagesframe.grid(row=0, column=1, sticky='nsw', pady=5)
        self.infoframe.grid(row=0, column=0, sticky='nsw', pady=5)

    def _create_stats(self):
        iff = self.infoframe
        self.iff_lbgrp = ttk.Label(iff, style='infoframe.TLabel', anchor="nw",
                                   text=f"Duplicates Group {self.g_iid[1:]}:")
        self.iff_lbnimages = ttk.Label(iff, style="infoframe.TLabel",
                                       anchor="w",)
        self.iff_lbsize = ttk.Label(iff, style="infoframe.TLabel", anchor="nw")

        self.iff_lbgrp.grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.iff_lbnimages.grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.iff_lbsize.grid(row=2, column=0, sticky='w', padx=10, pady=5)

    def _create_checkbuttons(self, with_image: bool = True):
        imf = self.imagesframe
        for mm, (fpath, fiid, fselected) in enumerate(
                zip(self.f_paths, self.f_iids, self.f_selected)):
            self.imf_checkvalues[fiid] = tk.IntVar(master=imf, value=fselected)
            if with_image:
                img = get_thumbnail(fpath)
                self.imf_thumbnails[fiid] = ImageTk.PhotoImage(img)
                self.imf_checkbuttons[fiid] = ttk.Checkbutton(
                    imf, text=fiid, image=self.imf_thumbnails[fiid],
                    variable=self.imf_checkvalues[fiid], compound="top")
            elif not with_image:
                self.imf_checkbuttons[fiid] = ttk.Checkbutton(
                    imf, text=fiid, variable=self.imf_checkvalues[fiid],
                    compound="top")
                self.imf_checkbuttons[fiid].grid(
                    row=0, column=mm, sticky='nsew', padx=(0, 5), pady=5)

            # Bind an event handler to each checkbutton
            self.imf_checkbuttons[fiid].bind(
                '<ButtonRelease-1>', self.indicate_checkbutton_toggled)

    def _update_stats(self):
        # 1. Update self.iff_lbnimages
        nfiles = len(self.f_paths)
        if nfiles >> 1:
            text = f'{nfiles} Pictures'
        else:
            text = f'{nfiles} Picture'
        self.iff_lbnimages["text"] = text

        # 2. Update self.iff_lbsize
        ts = self.total_size
        self.iff_lbsize["text"] = f'{ts[0]:.2f} {ts[1]}'

    def get_total_size(self):
        return filesize(sum([Path(i).stat().st_size for i in self.f_paths]))

    def indicate_checkbutton_toggled(self, event):
        self.master.toggled_checkbutton = event.widget
        self.master.event_generate("<<CheckbuttonToggled>>")

    def reset(self):
        # 1. Destroy children widgets
        self.infoframe.destroy()
        self.imagesframe.destroy()

        # Clear self.imagesframe attributes
        if self.imf_checkbuttons:
            self.imf_checkbuttons.clear()
        if self.imf_thumbnails:
            self.imf_thumbnails.clear()
        if self.imf_checkvalues:
            self.imf_checkvalues.clear()
