# print(f"{__name__}")

# Python modules
import tkinter as tk
import tkinter.ttk as ttk
from pathlib import Path
import concurrent.futures as cf
import queue
import threading
from itertools import repeat

# External Packages
from PIL import Image, ImageTk

# Project module
from adp.functions import filesize

__all__ = ["DupGroup", "get_thumbnail", "get_thumbnails_concurrently_with_queue",]
__version__ = '0.1'
__author__ = 'Chia Yan Hon, Julian.'
__copyright__ = "Copyright 2024, Chia Yan Hon, Julian."
__license__ = "Apache License, Version 2.0"


def get_thumbnail(fpath: str, psize=(200, 200)):
    """Function uses the Image module of the Pillow pkg to convert a photo to
    a thumbnail size photo and returns the thumbnail photo.

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

def get_thumbnail_c(giid: str, fiid: str, fpath: str, psize=(200, 200)):
    """Function uses the Image module of the Pillow pkg to convert a photo to
    a thumbnail size photo and returns the thumbnail photo along with it's
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

# def get_thumbnails_concurrently_with_queue(
#         g_iids: list, f_iids: list, f_paths:list, rqueue: queue.Queue):
#
#     def load_results_to_tqueue(future):
#         # print(f"def load_results_to_tqueue(future):")
#         # print(f"{threading.main_thread()=} {threading.current_thread()=}")
#         rqueue.put(("thumbnail", future.result()))
#         futures.remove(future)
#         if not futures:
#             # print(f'get_thumbnails_concurrently has completed!')
#             rqueue.put(("completed", ()))
#
#     size = (200, 200)
#     futures = []
#     job_fn = get_thumbnail_c
#     # print(f"{threading.main_thread()=} {threading.current_thread()=}")
#     # print(f'get_thumbnails_concurrently has started...')
#     # with cf.ProcessPoolExecutor() as vp_executor:
#     with cf.ThreadPoolExecutor() as vp_executor:
#         for giid, fiids, fpaths in zip(g_iids, f_iids, f_paths):
#             for gg, ff, pp in zip(repeat(giid, len(fiids)), fiids, fpaths):
#                 job_args = gg, ff, pp, size
#                 futures.append(vp_executor.submit(job_fn, *job_args))
#                 futures[-1].add_done_callback(load_results_to_tqueue)


def get_thumbnails_concurrently_with_queue(
        g_iids: list, f_iids: list, f_paths:list, rqueue: queue.Queue,
        size: tuple):
    futures = []
    job_fn = get_thumbnail_c
    # print(f"{threading.main_thread()=} {threading.current_thread()=}")
    # print(f'get_thumbnails_concurrently has started...')
    # with cf.ProcessPoolExecutor() as vp_executor:
    with cf.ThreadPoolExecutor() as vp_executor:
        for giid, fiids, fpaths in zip(g_iids, f_iids, f_paths):
            for gg, ff, pp in zip(repeat(giid, len(fiids)), fiids, fpaths):
                job_args = gg, ff, pp, size
                futures.append(vp_executor.submit(job_fn, *job_args))
    for future in cf.as_completed(futures):
        rqueue.put(("thumbnail", future.result()))
        futures.remove(future)
        if not futures:
            # print(f'get_thumbnails_concurrently has completed!')
            rqueue.put(("completed", ()))


class DupGroup(ttk.Frame):
    """A customised ttk.Frame widget that shows thumbnails of duplicated
    photos.

    Construction:
        It consists of 2 children ttk.Frame widgets gridded side-by-side:
        (1) Right ttk.frames (i.e. self.imagesframe):
            - consist of ttk.Checkbuttons that display the thumbnails and
              file item ID (i.e. fiid) of the duplicate photos. Their left to
              right ordering sequence denotes the oldest photo (i.e. original)
               to the latest photos (i.e. copies).
        (2) Left ttk.frames (i.e. self.infoframe):
            - consists of ttk.Labels that displays the group item id (giid),
              quantity and the total size of duplicate photos.

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
        self.bind("<Configure>", lambda _: self.update_idletasks())

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
            text = f'{nfiles} photos'
        else:
            text = f'{nfiles} photo'
        self.iff_lbnimages["text"] = text

        # 2. Update self.iff_lbsize
        ts = self.total_size
        self.iff_lbsize["text"] = f'{ts[0]:.2f} {ts[1]}'

        self.infoframe.lift()

    def destroy_checkbutton(self, fiid, fpath):
        """Delete the Checkbutton, tk.BooleanVar, thumbnail and filepath of
        fiid and update the widgets of self.infoframe."""
        # 1. Deletion tasks
        self.imf_checkbuttons[fiid].destroy()
        del self.imf_checkvalues[fiid]
        del self.imf_thumbnails[fiid]
        # 2. Update tasks
        self.f_iids.remove(fiid)
        self.f_paths.remove(fpath)
        self.total_size = self.get_total_size()
        self._update_stats()
        self.update_idletasks()
        if not self.f_iids:
            self.destroy()
            return "Destroyed self"
        else:
            return "Destroyed checkbutton"

    def get_total_size(self):
        return filesize(sum([Path(i).stat().st_size for i in self.f_paths]))

    def indicate_checkbutton_toggled(self, event):
        # print(f"\n{self} def indicate_checkbutton_toggled(self):")
        self.master.toggledcheckbutton = event.widget
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


if __name__ == '__main__':
    from adp.widgets import w_ttkstyle
    from time import perf_counter
    from constants import CWD
    import random
    from time import sleep

    geom = "1300x1080+0+0"
    gids = [f"G{i}" for i in range(10)]
    random.seed()
    fids = []
    selected = []
    fpaths = []
    print(CWD)
    photo = CWD / "widgets" / "testimage.jpg"
    print(f"{photo=})")
    for gid in gids:
        f_ids = []
        sel = []
        fps = []
        total = random.randint(2, 10)
        for i in range(total):
            f_ids.append(f"{gid}-P{i}")
            sel.append(0)
            fps.append(photo)
        fids.append(f_ids)
        selected.append(sel)
        fpaths.append(fps)


    # print()
    # Concurrent approach to create multiple DupGroup widgets with Checkbuttons
    start = perf_counter()
    root = tk.Tk()
    root.title('DupGroup - Concurrent Creation Of CheckButtons With Thumnbnail-'
               'Sized Image')
    root.geometry(geom)
    root.configure(background="blue")
    s = ttk.Style()
    style = w_ttkstyle.customise_ttk_widgets_style(s)

    def check_thread(thread, tqueue, dupgroups, start0):
        # print(f"\ndef _check_thread(self, thread, start0):")
        duration = 1  # millisecond
        try:
            info = tqueue.get(block=False)
        except queue.Empty:
            # let's try again later
            root.after(duration,
                       lambda: check_thread(thread, tqueue, dupgroups, start0))
        else:
            # print(f"self._check_thread got, {info=}")
            # Extract info from queue
            match info[0]:
                case "thumbnail":
                    giid, fiid, img = info[1]
                    dpgrps = dupgroups
                    dpgrps[giid].imf_thumbnails[fiid] = ImageTk.PhotoImage(img)
                    dpgrps[giid].imf_checkbuttons[fiid]["image"] = \
                        dpgrps[giid].imf_thumbnails[fiid]
                    root.after(duration, lambda: check_thread(thread, tqueue,
                                                              dupgroups, start0))
                case "completed":
                    end0 = perf_counter()
                    total_time = end0 - start0
                    print(f"Concurrent -: {total_time=}s")

    dupgroups = {}
    for n, (x, y, z, s) in enumerate(zip(gids, fids, fpaths, selected)):
        dupgroups[x] = DupGroup(root, x, y, z, s,False)
        dupgroups[x].grid(row=n, column=0, sticky='nsew')
    # print(f"{len(dupgroups)=} {dupgroups=}")

    # 3. Concurrently convert each photo duplicate to a thumbnail and
    #    include into the respective Checkbutton in the DupGroup widgets.
    thumbnails_queue = queue.Queue()
    tthread = threading.Thread(
        target=get_thumbnails_concurrently_with_queue,
        args=(gids, fids, fpaths, thumbnails_queue, (200, 200)),
        name="thumbnailthread")
    tthread.start()
    check_thread(tthread, thumbnails_queue, dupgroups, start)

    def exit_root():
        """Function to exit root window"""
        for group in dupgroups.values():
            group.reset()
        dupgroups.clear()
        root.destroy()
        root.quit()

    # Setup root window's shutdown and start it's main events loop
    root.protocol('WM_DELETE_WINDOW', exit_root)
    root.mainloop()


    # Serial approach to create multiple DupGroup widgets with Checkbuttons
    start = perf_counter()
    root = tk.Tk()
    root.title('DupGroup - Serial Creation Of CheckButtons With Thumnbnail-'
               'Sized Image')
    root.geometry(geom)
    root.configure(background="blue")
    s = ttk.Style()
    style = w_ttkstyle.customise_ttk_widgets_style(s)
    dupgroups = {}
    for n, (x, y, z, s) in enumerate(zip(gids, fids, fpaths,selected)):
        dupgroups[x] = DupGroup(root, x, y, z, s,True)
        dupgroups[x].grid(row=n, column=0, sticky='nsew')
    # print(f"{len(dupgroups)=} {dupgroups=}")

    end = perf_counter()
    total_time = end - start
    print(f"Serial -: {total_time=}s")

    def exit_root():
        """Function to exit root window"""
        for group in dupgroups.values():
            group.reset()
        dupgroups.clear()
        root.destroy()
        root.quit()

    # Setup root window's shutdown and start it's main events loop
    root.protocol('WM_DELETE_WINDOW', exit_root)
    root.mainloop()