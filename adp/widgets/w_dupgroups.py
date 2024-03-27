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

def get_thumbnails_concurrently_with_queue(
        g_iids: list, f_iids: list, f_paths:list, rqueue: queue.Queue):

    def load_results_to_tqueue(future):
        # print(f"def load_results_to_tqueue(future):")
        # print(f"{threading.main_thread()=} {threading.current_thread()=}")
        rqueue.put(("thumbnail", future.result()))
        futures.remove(future)
        if not futures:
            # print(f'get_thumbnails_concurrently has completed!')
            rqueue.put(("completed", ()))

    size = (200, 200)
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
                futures[-1].add_done_callback(load_results_to_tqueue)


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
                 f_selected: list, with_image=True, thumbnailsize=(200, 200),
                 **options):
        super().__init__(master, style='DupGroup.TFrame', **options)
        self.master = master
        self.g_iid = g_iid
        self.f_iids = f_iids
        self.f_paths = f_paths
        self.f_selected = f_selected
        self.thumbnailsize = thumbnailsize
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
    # from widgets.constants import *
    # gg_iids = ['G0', 'G1', 'G2', 'G2', 'G3', 'G4', 'G5']
    # ff_iids = [['G0_F0', 'G0_F1'], ['G1_F0', 'G1_F1'],
    #            ['G2_F0', 'G2_F1'], ['G3_F0', 'G3_F1'],
    #            ['G4_F0', 'G4_F1'], ['G5_F0', 'G5_F1']]
    # vvsiids = ['G0_F1', 'G1_F1', 'G2_F1', 'G2_F2', 'G3_F1', 'G3_F2', 'G4_F1',
    #            'G5_F1']
    # pdir = str(CWD)
    # ff_paths = [
    #         [pdir + '/Samples/Photos3/Wallpapers_Grub2_old'
    #                 '/BootScreen_EliotTesla.png',
    #          pdir + '/Samples/Photos3/Wallpapers_Grub2/'
    #                 'BootScreen_EliotTesla.png'],
    #         [pdir + '/Samples/Photos3/Wallpapers_Grub2_old/fNuD4F.jpg',
    #          pdir + '/Samples/Photos3/Wallpapers_Grub2/fNuD4F.jpg'],
    #         [pdir + '/Samples/Photos3/Wallpapers_Grub2_old'
    #                 '/PowerButton1920x1080.jpg',
    #          pdir + '/Samples/Photos3/Wallpapers_Grub2/PowerButton1920x1080'
    #                 '.jpg'],
    #         [pdir + '/Samples/Photos3/Wallpapers_Grub2_old/Sierra2.png',
    #          pdir + '/Samples/Photos3/Wallpapers_Grub2/Sierra2.png'],
    #         [pdir + '/Samples/Photos3/Wallpapers_Grub2_old'
    #                 '/wp2958180_1920x1080.png',
    #          pdir + '/Samples/Photos3/Wallpapers_Grub2/wp2958180_1920x1080'
    #                 '.png'],
    #         [pdir + '/Samples/Photos3/Wallpapers_Grub2_old/wp2958180-worship'
    #                 '-wallpaper.jpg',
    #          pdir + '/Samples/Photos3/Wallpapers_Grub2/wp2958180-worship'
    #                 '-wallpaper.jpg']
    #     ]

    gg_iids = [
        'G0', 'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9', 'G10',
        'G11', 'G12', 'G13', 'G14', 'G15', 'G16', 'G17', 'G18', 'G19', 'G20',
        'G21', 'G22', 'G23', 'G24', 'G25', 'G26', 'G27', 'G28', 'G29'
    ]
    ff_iids = [
        ('G0_F0', 'G0_F1'), ('G1_F0', 'G1_F1'),
        ('G2_F0', 'G2_F1', 'G2_F2', 'G2_F3'),
        ('G3_F0', 'G3_F1', 'G3_F2', 'G3_F3'),
        ('G4_F0', 'G4_F1', 'G4_F2', 'G4_F3', 'G4_F4', 'G4_F5'),
        ('G5_F0', 'G5_F1', 'G5_F2', 'G5_F3', 'G5_F4', 'G5_F5'),
        ('G6_F0', 'G6_F1'), ('G7_F0', 'G7_F1'), ('G8_F0', 'G8_F1'),
        ('G9_F0', 'G9_F1'), ('G10_F0', 'G10_F1'), ('G11_F0', 'G11_F1'),
        ('G12_F0', 'G12_F1'), ('G13_F0', 'G13_F1'), ('G14_F0', 'G14_F1'),
        ('G15_F0', 'G15_F1'), ('G16_F0', 'G16_F1'), ('G17_F0', 'G17_F1'),
        ('G18_F0', 'G18_F1'), ('G19_F0', 'G19_F1'), ('G20_F0', 'G20_F1'),
        ('G21_F0', 'G21_F1'), ('G22_F0', 'G22_F1'), ('G23_F0', 'G23_F1'),
        ('G24_F0', 'G24_F1'), ('G25_F0', 'G25_F1'), ('G26_F0', 'G26_F1'),
        ('G27_F0', 'G27_F1'), ('G28_F0', 'G28_F1'), ('G29_F0', 'G29_F1')
    ]
    source = '/home/master/Coding/PycharmProjects/ADP/Samples/Photos4'
    ff_paths = [
        [
            source + '/Wallpapers_old/Apartments/pebbles-apartments-nice-living-area-p.webp',
            source + '/Wallpapers/Apartments/pebbles-apartments-nice-living-area-p.webp'],
        [
            source + '/Wallpapers_old/Apartments/maxresdefault.jpg',
            source + '/Wallpapers/Apartments/maxresdefault.jpg'],
        [
            source + '/Wallpapers_old/Apartments/Clean-Apartment-Interior-Design.jpeg',
            source + '/Wallpapers_old/Apartments/Clean-Apartment-Interior-Design-2.jpeg',
            source + '/Wallpapers/Apartments/Clean-Apartment-Interior-Design.jpeg',
            source + '/Wallpapers/Apartments/Clean-Apartment-Interior-Design-2.jpeg'],
        [
            source + '/Wallpapers_old/demo/Milaidhoo-Island-Maldives-Beach-Bedroom-Feat.jpg',
            source + '/Wallpapers_old/Milaidhoo-Island-Maldives-Beach-Bedroom-Feat.jpg',
            source + '/Wallpapers/demo/Milaidhoo-Island-Maldives-Beach-Bedroom-Feat.jpg',
            source + '/Wallpapers/Milaidhoo-Island-Maldives-Beach-Bedroom-Feat.jpg'],
        [
            source + '/Wallpapers_old/demo/copy.jpg',
            source + '/Wallpapers_old/demo/dog-1920x1080-puppy-white-animal-pet-beach-sand-sea-1611.jpg',
            source + '/Wallpapers_old/dog-1920x1080-puppy-white-animal-pet-beach-sand-sea-1611.jpg',
            source + '/Wallpapers/demo/copy.jpg',
            source + '/Wallpapers/demo/dog-1920x1080-puppy-white-animal-pet-beach-sand-sea-1611.jpg',
            source + '/Wallpapers/dog-1920x1080-puppy-white-animal-pet-beach-sand-sea-1611.jpg'],
        [
            source + '/Wallpapers_old/demo/Sierra2.jpg',
            source + '/Wallpapers_old/HighSierra-wallpapers/Sierra 2.jpg',
            source + '/Wallpapers_old/Sierra2.jpg',
            source + '/Wallpapers/demo/Sierra2.jpg',
            source + '/Wallpapers/HighSierra-wallpapers/Sierra 2.jpg',
            source + '/Wallpapers/Sierra2.jpg'],
        [
            source + '/Wallpapers_old/Screenshot from 2020-09-04 14-02-37.png',
            source + '/Wallpapers/Screenshot from 2020-09-04 14-02-37.png'],
        [
            source + '/Wallpapers_old/Zoom/room.jpg',
            source + '/Wallpapers/Zoom/room.jpg'],
        [
            source + '/Wallpapers_old/Apartments/MPM94144.jpg',
            source + '/Wallpapers/Apartments/MPM94144.jpg'],
        [
            source + '/Wallpapers_old/Apartments/98758711.jpg',
            source + '/Wallpapers/Apartments/98758711.jpg'],
        [
            source + '/Wallpapers_old/Screenshot from 2020-09-04 14-02-03.png',
            source + '/Wallpapers/Screenshot from 2020-09-04 14-02-03.png'],
        [
            source + '/Wallpapers_old/HighSierra-wallpapers/High Sierra.jpg',
            source + '/Wallpapers/HighSierra-wallpapers/High Sierra.jpg'],
        [
            source + '/Wallpapers_old/HighSierra-wallpapers/Sierra.jpg',
            source + '/Wallpapers/HighSierra-wallpapers/Sierra.jpg'],
        [
            source + '/Wallpapers_old/pexels-eberhard-grossgasteiger-443446.jpg',
            source + '/Wallpapers/pexels-eberhard-grossgasteiger-443446.jpg'],
        [
            source + '/Wallpapers_old/Screenshot from 2020-09-04 14-01-42.png',
            source + '/Wallpapers/Screenshot from 2020-09-04 14-01-42.png'],
        [
            source + '/Wallpapers_old/Wavesurfer.png',
            source + '/Wallpapers/Wavesurfer.png'],
        [
            source + '/Wallpapers_old/pexels-scott-webb-1931143.jpg',
            source + '/Wallpapers/pexels-scott-webb-1931143.jpg'],
        [
            source + '/Wallpapers_old/pexels-zaksheuskaya-1616403.jpg',
            source + '/Wallpapers/pexels-zaksheuskaya-1616403.jpg'],
        [
            source + '/Wallpapers_old/ElizabethandTeam.JPG',
            source + '/Wallpapers/ElizabethandTeam.JPG'],
        [
            source + '/Wallpapers_old/Screenshot from 2020-09-04 14-01-33.png',
            source + '/Wallpapers/Screenshot from 2020-09-04 14-01-33.png'],
        [
            source + '/Wallpapers_old/dmb_Gollinger_Wasserfall_Austria.jpg',
            source + '/Wallpapers/dmb_Gollinger_Wasserfall_Austria.jpg'],
        [
            source + '/Wallpapers_old/dmb_vandusenbotanicalgarden.jpg',
            source + '/Wallpapers/dmb_vandusenbotanicalgarden.jpg'],
        [
            source + '/Wallpapers_old/Mountains_Sunset.jpg',
            source + '/Wallpapers/Mountains_Sunset.jpg'],
        [
            source + '/Wallpapers_old/green_dears_forest.jpg',
            source + '/Wallpapers/green_dears_forest.jpg'],
        [
            source + '/Wallpapers_old/pexels-pixabay-459203.jpg',
            source + '/Wallpapers/pexels-pixabay-459203.jpg'],
        [
            source + '/Wallpapers_old/pexels-mia-von-steinkirch-3894157.jpg',
            source + '/Wallpapers/pexels-mia-von-steinkirch-3894157.jpg'],
        [
            source + '/Wallpapers_old/pexels-tara-winstead-7723324.jpg',
            source + '/Wallpapers/pexels-tara-winstead-7723324.jpg'],
        [
            source + '/Wallpapers_old/pexels-luis-del-río-15286.jpg',
            source + '/Wallpapers/pexels-luis-del-río-15286.jpg'],
        [
            source + '/Wallpapers_old/tree.jpg',
            source + '/Wallpapers/tree.jpg'],
        [
            source + '/Wallpapers_old/dmb_pexels-pixabay-358482.jpg',
            source + '/Wallpapers/dmb_pexels-pixabay-358482.jpg']
    ]

    ff_selected = [
        (1, 0), (1, 0), (1, 0, 0, 0), (1, 0, 0, 0), (1, 0, 0, 0, 0, 0),
        (1, 0, 0, 0, 0, 0), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0),
        (1, 0), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0),  (1, 0), (1, 0), (1, 0),
        (1, 0), (1, 0), (1, 0), (1, 0), (1, 0), (1, 0),  (1, 0), (1, 0), (1, 0)
    ]

    from adp.widgets import w_ttkstyle
    from time import perf_counter

    geom = "1300x1080+0+0"

    print()
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
    for n, (x, y, z, s) in enumerate(zip(gg_iids, ff_iids, ff_paths,
                                         ff_selected)):
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

    # Setup root window's shutdown and start it's main events loop
    root.protocol('WM_DELETE_WINDOW', exit_root)
    root.mainloop()



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
    for n, (x, y, z, s) in enumerate(zip(gg_iids, ff_iids, ff_paths,
                                         ff_selected)):
        dupgroups[x] = DupGroup(root, x, y, z, s,False)
        dupgroups[x].grid(row=n, column=0, sticky='nsew')
    # print(f"{len(dupgroups)=} {dupgroups=}")

    # 3. Concurrently convert each photo duplicate to a thumbnail and
    #    include into the respective Checkbutton in the DupGroup widgets.
    thumbnails_queue = queue.Queue()
    tthread = threading.Thread(
        target=get_thumbnails_concurrently_with_queue,
        args=(gg_iids, ff_iids, ff_paths, thumbnails_queue),
        name="thumbnailthread")
    tthread.start()
    check_thread(tthread, thumbnails_queue, dupgroups, start)


    def exit_root():
        """Function to exit root window"""
        for group in dupgroups.values():
            group.reset()
        dupgroups.clear()
        root.destroy()

    # Setup root window's shutdown and start it's main events loop
    root.protocol('WM_DELETE_WINDOW', exit_root)
    root.mainloop()


