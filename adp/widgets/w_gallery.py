# print(f"{__name__}")

# Python modules
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
from time import perf_counter
import threading
import queue

# External Packages
from PIL import ImageTk

# Project modules
from adp.functions import timings
from adp.widgets.constants import DFONT, BFONT, FG, BG, BG2, CWD
from adp.widgets.w_table import Table
from adp.widgets.w_scrframe import VerticalScrollFrame
from adp.widgets.w_dupgroups import (DupGroup,
                                     get_thumbnails_concurrently_with_queue)

__all__ = ["Gallery"]
__version__ = '0.1'
__author__ = 'Chia Yan Hon, Julian.'
__copyright__ = "Copyright 2024, Chia Yan Hon, Julian."
__license__ = "Apache License, Version 2.0"

dfont = list(DFONT.values())
bfont = list(BFONT.values())


class Gallery(ttk.PanedWindow):
    """A custom ttk.PanedWindow widget that consist of a custom Table widget
    and a custom VerticalScrollFrame widget. The Table widget displays
    information of some of the detected duplicated raster images in a treeview
    format whereas the VerticalScrollFrame widget acts as a viewport to display
    the same information in an organised thumbnail format.

    User Methods:
    .reset_viewport() - reset self.dupgroupsframe, self.dupgroups and
                        self.viewport

    Generated Virtual Events:
    "<<DupGroupsCreated>>" - whenever the creation of a batch of Dupgroup
                             instances in self.dupgroupsframe is completed
    """

    def __init__(self, master, **options):
        try:
            debug = options.pop("debug")
        except KeyError:
            self.debug = False
        else:
            if isinstance(debug, bool):
                self.debug = debug
            else:
                raise TypeError
        super().__init__(master, **options)
        self.master = master

        self._thumbnails_queue = queue.Queue()
        self.dupgroups = {}  # to contain all giids and their DupGroup instances
        self.dupgroupsframe = None  # widget: parent of all DupGroup instances
        self.table = None  # widget: Table instance
        self.viewport = None  # widget: VerticalScrollFrame instance

        self._create_widget()
        self._create_bindings()

    def _create_widget(self):
        self.table = Table(self, debug=self.debug)

        self.viewport = VerticalScrollFrame(
            self, background=BG2, troughcolor="grey", arrowcolor=FG,
            mainborderwidth=1, interiorborderwidth=0, mainrelief='sunken',
            interiorrelief='sunken')
        self.viewport.vscrollbar["style"] = "Vertical.TScrollbar"
        self.viewport.hscrollbar["style"] = "Horizontal.TScrollbar"
        self.viewport.interior.toggledcheckbutton = None

        self.add(self.table)
        self.add(self.viewport)

        self._create_dupgroupframe()

    def _create_dupgroupframe(self):
        """This ttk.Frame is the primary container of all DupGroup widget
        instances. It is the only child of self.view port.interior. Every
        time a full reset of the viewport is needed, this widget will be
        destroyed and recreated to store a new batch of DupGroup widget
        instances."""
        self.dupgroupsframe = ttk.Frame(self.viewport.interior)
        self.dupgroupsframe.grid(row=0, column=0, sticky="nsew")
        self.dupgroupsframe.toggled_checkbutton = None

    def reset_viewport(self):
        # print(f"\n{self=} def reset_viewport(self, event):")
        # print(f"{self.viewport.interior.winfo_children()=}")
        if not self.dupgroups:
            return

        # 1. Destroy self.dupgroupsframe and recreate it.
        self.dupgroupsframe.destroy()
        self._create_dupgroupframe()

        # 2. Clear self.dupgroups
        self.dupgroups.clear()

        # 3. Reset viewport
        self.viewport.interior["width"] = 10
        self.viewport.interior["height"] = 10
        self.viewport.update_idletasks()
        self.viewport.canvas.yview(tk.MOVETO, 0.0)
        self.viewport.interior.toggledcheckbutton = None

    def _destroy_dupgroups_for_giids(self, giids: list[str]):
        # print(f"_destroy_dupgroups_for_giids {giids}")
        for giid in giids:
            self.dupgroups[giid].destroy()
            del self.dupgroups[giid]

    def _create_dupgroups_for_giids(self, g_iids: list[str]):
        """Method to create DupGroup instances inside of self.dupgroupsframe
        for a list of group item ids."""
        # print(f"\ndef _create_dupgroups_for_giids(self, giids):")
        start0 = perf_counter()
        dgf = self.dupgroupsframe
        db = self.table.sql3db

        # 2. Create the DupGroup widget for each giid
        f_iids = [db.get_item_ids_of_group(giid) for giid in g_iids]
        f_paths = [db.get_full_paths_of_group(giid) for giid in g_iids]
        f_selected = [db.get_selected_of_group(giid) for giid in g_iids]
        # print(f"{len(g_iids)=} {g_iids}")
        # print(f"{len(f_iids)=} {f_iids}")
        # print(f"{len(f_paths)=}")
        # print(f"{len(f_selected)=} {f_selected}")
        for giid, fiids, fpaths, fselected in zip(g_iids, f_iids, f_paths,
                                                  f_selected):
            self.dupgroups[giid] = DupGroup(dgf, giid, fiids, fpaths, fselected,
                                            # with_image=True,
                                            with_image=False,
                                            )
            row = int(giid[1:])
            self.dupgroups[giid].grid(row=row, column=0, sticky='nsew')
            self.dupgroups[giid].update_idletasks()
        # print(f"{len(self.dupgroups)=}")

        # 3. Concurrently convert each photo duplicate to a thumbnail and
        #    include into the respective Checkbutton in the DupGroup widgets.
        tthread = threading.Thread(
            target=get_thumbnails_concurrently_with_queue,
            args=(g_iids, f_iids, f_paths, self._thumbnails_queue),
            name="thumbnailthread")
        tthread.start()
        self._check_thumbnails_queue(tthread, start0)

    def _check_thumbnails_queue(self, thread, start0):
        # print(f"\ndef _check_thread(self, thread, start0):")
        duration = 1  # millisecond
        try:
            info = self._thumbnails_queue.get(block=False)
        except queue.Empty:
            # let's try again later
            self.after(duration,
                       lambda: self._check_thumbnails_queue(thread, start0))
        else:
            # print(f"self._check_thread got, {info=}")
            # Extract info from queue
            match info[0]:
                case "thumbnail":
                    giid, fiid, img = info[1]
                    dpgrps = self.dupgroups
                    dpgrps[giid].imf_thumbnails[fiid] = ImageTk.PhotoImage(img)
                    dpgrps[giid].imf_checkbuttons[fiid]["image"] = \
                        dpgrps[giid].imf_thumbnails[fiid]
                    self.after(duration,
                               lambda: self._check_thumbnails_queue(thread,
                                                                    start0))
                case "completed":
                    # 3. Show the 1st DupGroup instance
                    self.viewport.canvas.update_idletasks()
                    self.viewport.canvas.yview(tk.MOVETO, 0.0)
                    self.viewport.interior.update_idletasks()
                    end0 = perf_counter()
                    loadtime = end0 - start0
                    tl, tl_units = timings(loadtime)
                    print(f'New Dupgroups instances created in '
                          f'{tl:.6f} {tl_units}.')
                    self.dupgroupsframe.event_generate("<<DupGroupsCreated>>",
                                                       when="tail")

    def _create_bindings(self):
        table = self.table
        tree = self.table.tree
        # interior = self.viewport.interior

        # 1. Create DupGroup instances in self.dupgroupframe for current and
        #    next shpwn pages after self.table.tree is populated for the
        #    first time.
        tree.bind("<<TreePopulatedFirstTimeDone>>",
                  self._event_create_dupgroups_of_shown_giids)

        # 2. Reset self.viewport.interior after resetting self.table
        table.bind("<<TableResetDone>>", self._event_reset_viewport)

        # 3. Ensure Viewport 1st visible DupGroup instance correspond to the
        #    1st visible group item in the Treeview.
        tree.bind("<<TreeScrollUpDone>>",
                  self._event_show_1st_visible_treeview_groupitem_in_viewport)
        tree.bind("<<TreeScrollDownDone>>",
                  self._event_show_1st_visible_treeview_groupitem_in_viewport)
        tree.bind("<<TreeStartReached>>",
                  self._event_show_1st_visible_treeview_groupitem_in_viewport)
        tree.bind("<<TreeEndReached>>",
                  self._event_show_1st_visible_treeview_groupitem_in_viewport)
        self.dupgroupsframe.bind(
            "<<DupGroupsCreated>>",
            self._event_show_1st_visible_treeview_groupitem_in_viewport)

        # 4. Create & delete dupgroups during page transitions
        tree.bind("<<TreePopulateNextNextPageDone>>",
                  self._event_dupgroups_page_forward)
        tree.bind("<<TreeReattachNextNextPageDone>>",
                  self._event_dupgroups_page_forward)
        tree.bind("<<TreeReattachPreviousPreviousPageDone>>",
                  self._event_dupgroups_page_backward)

        # 5. Update the checkboxes of each DupGroup instance whenever one or
        #    more Treeview item is/are toggled.
        tree.bind("<<TreeFileItemsToggled>>",
                  self._event_update_dupgroups_checkvalues)

        # 6. Ensure that clicked file item in the treeview (i.e.self.table.tree)
        #    moves the corresponding DupGroup instance to the top of the
        #    viewport.
        tree.bind("<<MoveDupGroupToTop>>",
                  self._event_move_dupgroup_to_top_of_viewport)

        # 7. Update the tags of the file item in the Treeview corresponding to
        #    the toggled Checkbutton and ensure the group item and all its
        #    file items are visible in the Treeview.
        self.dupgroupsframe.bind("<<CheckbuttonToggled>>",
                                 self._event_toggle_tree_file_item_appearance)

    def _event_create_dupgroups_of_shown_giids(self, event):
        # print(f"\ndef _event_create_dupgroups_of_shown_giids(self, event):")
        giids = [giid for giids in self.table.shown_giids for giid in giids]
        self._create_dupgroups_for_giids(giids)

    def _event_reset_viewport(self, event):
        self.reset_viewport()
        self._create_bindings()

    def _event_show_1st_visible_treeview_groupitem_in_viewport(self, event):
        """Event handler to ensure the Viewport 1st visible DupGroup
        instance correspond to the 1st visible group item in the Treeview.
        """
        # print(f"\ndef _event_show_1st_visible_treeview_groupitem_in_viewport("
        #       f"self, event)")
        vgiids = self.table.get_visible_group_iids()
        # print(f"{vgiids=}")
        # print(f"{self.dupgroups.keys()=}")
        self.viewport.update_idletasks()
        first_tn_y = self.dupgroups[vgiids[0]].winfo_y()
        tnf_height = self.viewport.interior.winfo_reqheight()
        # print(f"{first_tn_y/tnf_height=}")
        self.viewport.canvas.yview_moveto(first_tn_y / tnf_height)

    def _event_dupgroups_page_forward(self, event):
        # print(f"\ndef _event_dupgroups_page_forward(self, event):")
        # for n, giids in enumerate(self.table.shown_giids):
        #     print(n, giids)
        # 1. Destroy previous previous page
        pppage = self.table.shown_pages[0] - 1
        # print(f"{pppage=}")
        pppage_giids = self.table.sql3db.get_group_ids_of_page(pppage)
        # print(f"{pppage_giids=}")
        if pppage_giids:
            self._destroy_dupgroups_for_giids(pppage_giids)
        # 2. Create next page
        nnpage_giids = self.table.shown_giids[2]
        self._create_dupgroups_for_giids(nnpage_giids)

    def _event_dupgroups_page_backward(self, event):
        # print(f"\ndef _event_dupgroups_page_backward(self, event):")
        # for n, giids in enumerate(self.table.shown_giids):
        #     print(n, giids)
        # 1. Destroy next next page
        nnpage = self.table.shown_pages[2] + 1
        # print(f"{nnpage=}")
        nnpage_giids = self.table.sql3db.get_group_ids_of_page(nnpage)
        # print(f"{nnpage_giids=}")
        if nnpage_giids:
            self._destroy_dupgroups_for_giids(nnpage_giids[-1:None:-1])
        # 2. Recreate new previous page
        pppage_giids = self.table.shown_giids[0]
        self._create_dupgroups_for_giids(pppage_giids[-1:None:-1])

    def _event_update_dupgroups_checkvalues(self, event):
        """Event handler to update the checkbox of every Checkbutton of every
         DupGroup instances."""
        # print(f"\ndef _event_update_dupgroups_checkvalues(self):")
        db = self.table.sql3db

        # 1. Get selected and unselected fiids from sql
        sel_fiids = list(db.get_selected().keys())
        unsel_fiids = list(db.get_selected(value=False).keys())
        # print(f"{len(sel_fiids)} {sel_fiids=}")
        # print(f"{len(unsel_fiids)} {unsel_fiids=}")

        # 2. Get their corresponding unique giids
        unique_sel_giids = set([i[:i.index("_")] for i in sel_fiids])
        unique_unsel_giids = set([i[:i.index("_")] for i in unsel_fiids])
        # print(f"{len(unique_sel_giids)} {unique_sel_giids=}")
        # print(f"{len(unique_unsel_giids)} {unique_unsel_giids=}")

        # 3. Extract those giids that were ever populated in the treeview
        shown_giids = [giid for giids in self.table.shown_giids for giid in
                       giids]
        shown_giids_sel = unique_sel_giids.intersection(set(shown_giids))
        shown_giids_unsel = \
            unique_unsel_giids.intersection(set(shown_giids))
        # print(f"{len(shown_giids_sel)} {shown_giids_sel=}")
        # print(f"{len(shown_giids_unsel)} {shown_giids_unsel=}")

        # 4. Extract those fiids that were ever populated in the treeview
        shown_fiids_sel = [i for i in sel_fiids if i[:i.index("_")] in
                           shown_giids_sel]
        shown_fiids_unsel = [i for i in unsel_fiids if i[:i.index("_")] in
                             shown_giids_unsel]
        # print(f"{len(shown_fiids_sel)} {shown_fiids_sel=}")
        # print(f"{len(shown_fiids_unsel)} {shown_fiids_unsel=}")

        # 5. Update the checkvalues of each CheckButton (cb) in all Dupgroup
        #    instances (regardless of whether they are visible or hidden).
        # Selected fiids
        for fiid in shown_fiids_sel:
            giid = fiid[:fiid.index("_")]
            self.dupgroups[giid].imf_checkvalues[fiid].set(True)
        # Unselected fiids
        for fiid in shown_fiids_unsel:
            giid = fiid[:fiid.index("_")]
            self.dupgroups[giid].imf_checkvalues[fiid].set(False)

    def _event_move_dupgroup_to_top_of_viewport(self, event):
        """Event handler to ensure the Viewport 1st visible DupGroup instance
         correspond to the group of the clicked file item in the Treeview."""
        # print(f"\ndef _event_move_dupgroup_to_top_of_viewport(self, event):")
        fiid = self.table.clicked_f_items[0]
        giid = self.table.sql3db.get_group_id_of_item(fiid)
        dg_y = self.dupgroups[giid].winfo_y()
        dgf_height = self.viewport.interior.winfo_reqheight()
        # print(f"{giid=}")
        # print(f"{dg_y/dgf_height=}")
        self.viewport.canvas.yview_moveto(dg_y / dgf_height)

    def _event_toggle_tree_file_item_appearance(self, event):
        # print(f"\ndef _toggle_tree_file_item_appearance(self, event):")
        table = self.table
        db = self.table.sql3db

        # 1. Get fiid of clicked Checkbutton
        fiid = event.widget.toggledcheckbutton.cget('text')
        # print(f"{type(fiid)=} {fiid=}")

        # 2. Toggle the fiid's selected value in the sql_database
        db.toggle_selected_of_item(fiid)

        # 3. Update the fiid's appearance/tags in the Treeview
        table.update_file_item_tags(fiid)

        # 4. Ensure all file items similar to fiid and their group item are
        #    visible in the Treeview.
        giid = db.get_group_id_of_item(fiid)
        fiids = db.get_item_ids_of_group(giid)
        for iid in fiids[-1::-1]:
            table.tree.see(iid)
        table.tree.see(giid)

        # 5. Update the state of delete button in self.table
        table.update_bn_delete_state()


class App(ttk.Frame):
    def __init__(self, master, **options):
        self.master = master
        # 1. Define attributes self.etype, self.layout and self.orient
        try:
            cfe = options.pop("cfe")
        except KeyError:
            self.cfe = "thread"  # default value
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
        # Define self.orient
        match self.layout:
            case "vertical":
                self.orient = "vertical"
            case "horizontal":
                self.orient = "horizontal"
        super().__init__(master, **options)
        self._create_widgets()
        self._create_bindings()

    def _create_widgets(self):
        self.find = Find(self, cfe=self.cfe, layout=self.layout)
        self.find.hide_selected_path()

        self.gallery = Gallery(self, orient=self.orient)
        table = self.gallery.table
        table.set_sdir(self.find.selected_dir)
        table.set_sql3db(self.find.sqlite3_db)

        self.find.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        if self.layout in "vertical":
            self.gallery.grid(row=0, column=1, sticky="nsew", padx=(0, 10),
                              pady=10)
            self.columnconfigure(1, weight=1)
            self.rowconfigure(0, weight=1)
            self.winfo_toplevel().minsize(width=1000, height=600)
        elif self.layout in "horizontal":
            self.gallery.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
            self.columnconfigure(0, weight=1)
            self.rowconfigure(1, weight=1)
            self.winfo_toplevel().minsize(width=1200, height=500)

    def _create_bindings(self):
        self.find.unbind("<<DirectorySelected>>")
        self.find.bind("<<DirectorySelected>>", self.event_reset_app)
        self.find.bind("<<Sqlite3DBPopulated>>",
                       self.gallery.table.event_populate_tree_the_first_time)
        self.gallery.table.bn_delete.bind("<<DeletionDone>>",
                                          self.event_recheck)

    def event_reset_app(self, event):
        # print(f"\ndef reset_app(self, event):")
        # 2. Reset Table
        table = self.gallery.table
        if table.tree.get_children():
            # print(f"Reset table")
            table.reset_table()
        self.after_idle(table.set_tree_column0_heading_text, table.sdir.get())
        self.gallery.update_idletasks()
        # 1. Enable find button
        # self.after_idle(self.find.bn_find.instate, ["disabled"],
        #                 self.find.enable_find_button)
        self.after_idle(self.find.enable_find_button)

    def event_recheck(self, event):
        # print(f"\ndef event_recheck(self, event):")
        print(f"\nRecheck {self.find.selected_dir.get()}")
        self.find.reset()
        self.event_reset_app(event)
        self.after_idle(self.find.bn_find.invoke)

    def exit(self):
        self.find.exit()


if __name__ == '__main__':
    import w_ttkstyle
    from adp.widgets.w_find import Find

    root = tk.Tk()
    root["background"] = BG
    root.title('ANY DUPLICATED PHOTOS?')
    root.geometry('1300x600')

    # Commands to create icon
    app_icon = str(CWD) + "/icons/app/ADP.png"
    wm_icon = ImageTk.PhotoImage(file=app_icon)
    wm_icon.image = app_icon
    root.tk.call('wm', 'iconphoto', root, wm_icon)

    s = ttk.Style()
    style = w_ttkstyle.customise_ttk_widgets_style(s)

    app = App(root, cfe="thread", layout="horizontal")  # stable
    app = App(root, cfe="process", layout="horizontal")  # hangs randomly after several reruns
    app.grid(row=0, column=0, sticky="nsew")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)


    def exit_root():
        """Function for shutting down root window"""
        mbox = messagebox.askokcancel("Quit",
                                      f"\nShut down ADP?\n",
                                      icon="question", default="ok")
        if mbox:
            print(f"\nExiting Application...")
            app.exit()
            root.destroy()


    # Setup root window's shutdown and start it's main events loop
    root.protocol('WM_DELETE_WINDOW', exit_root)

    root.mainloop()
