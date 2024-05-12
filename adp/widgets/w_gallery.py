# Python modules
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
import threading
import queue
from time import perf_counter
import gc
import os

# External Packages
from PIL import ImageTk

# Project modules
from adp.functions.tools import timings, pop_kwargs
from adp.widgets.constants import DFONT, BFONT, FG, BG, BG2, CWD
from adp.widgets.w_table import Table
from adp.widgets.w_scrframe import VerticalScrollFrame
from adp.widgets.w_dupgroups import (DupGroup,
                                     get_thumbnails_concurrently_with_queue)

__all__ = ["Gallery"]
__version__ = '0.1'
__license__ = "Apache License, Version 2.0"
__copyright__ = "Copyright 2024, Chia Yan Hon, Julian."
__author__ = 'Chia Yan Hon, Julian.'
__email__ = "julianchiayh@gmail.com"


dfont = list(DFONT.values())
bfont = list(BFONT.values())


class Gallery(Table):
    """A modified Table widget. It has an added pane that has a custom
    VerticalScrollFrame widget to acts as a viewport to display the
    information in self.tree in an organised thumbnail format.

    User Methods:
    .reset_viewport() - reset self.dupgroupsframe and self.viewport

    Generated Virtual Events:
    "<<DupGroupsCreated>>" - whenever the creation of a batch of Dupgroup
                             instances in self.dupgroupsframe is completed
    """

    def __init__(self, master, **options):
        self._cfe = pop_kwargs("cfe", ["process", "thread"], options)
        super().__init__(master, **options)

        self.viewport = None  # widget: VerticalScrollFrame instance
        self.dupgroupsframe = None  # widget: parent of all DupGroup instances
        self.vplabel = None

        self._after_id_dupgroups_paging = None
        self._after_id_update_dupgroups_checkvalues = None
        self._after_id_move_dupgroup_to_top_of_viewport = None
        self._thumbnails_queue = queue.Queue()
        self._exitevent = threading.Event()  # for graceful exit
        self._tthread = None
        self._start0 = None

        self._create_viewport()
        self.create_tree_bindings_part_2()
        self._create_dupgroupframe()
        self._create_dupgroupsframe_bindings()
        self._create_vplabel()

    def _create_viewport(self) -> None:
        self.viewport = VerticalScrollFrame(
            self, background=BG2, cbackground=BG2, ibackground=BG2,
            troughcolor="grey", arrowcolor=FG, mainborderwidth=1,
            interiorborderwidth=0, mainrelief='sunken', interiorrelief='sunken')
        self.viewport.vscrollbar["style"] = "Vertical.TScrollbar"
        self.viewport.hscrollbar["style"] = "Horizontal.TScrollbar"
        self.add(self.viewport)

    def _create_vplabel(self) -> None:
        self.vplabel = ttk.Label(self, style="vp.TLabel", anchor="center",
                                 text="Updating ....",
                                 font=('URW Gothic L', 15, 'normal'))
        self.vplabel.place(relx=0.5, rely=0.5, relwidth=1.0,  relheight=1.01,
                           anchor='center', in_=self.viewport)
        self.vplabel.lower(self.viewport)

    def _create_dupgroupframe(self) -> None:
        """This ttk.Frame is the primary container of all DupGroup widget
        instances. It is the only child of self.view port.interior. Every
        time a full reset of the viewport is needed, this widget will be
        destroyed and recreated to store a new batch of DupGroup widget
        instances."""
        # print(f"{threading.main_thread()=} {threading.current_thread()=}")
        # print(f"{threading.active_count()=} {threading.enumerate()=}")
        self.dupgroupsframe = ttk.Frame(self.viewport.interior)
        self.dupgroupsframe.grid(row=0, column=0, sticky="nsew")
        self.dupgroupsframe.toggled_checkbutton = None
        self.dupgroupsframe.dupgroups = {}  # to contain all giids and their DupGroup instances

    def reset_viewport(self) -> None:
        if not self.dupgroupsframe.dupgroups:
            return

        # 1. Destroy self.dupgroupsframe and recreate it.
        self.dupgroupsframe.destroy()
        gc.collect()  # Needed.
        self._create_dupgroupframe()
        self._create_dupgroupsframe_bindings()

        # 2. Reset viewport
        self.viewport.interior["width"] = 10
        self.viewport.interior["height"] = 10
        self.viewport.canvas.yview(tk.MOVETO, 0.0)
        self._after_id_dupgroups_paging = None
        self._after_id_update_dupgroups_checkvalues = None
        self._after_id_move_dupgroup_to_top_of_viewport = None

    def create_or_reattach_next_next_page(self, visible_giids, visible_fiids)\
            -> None:
        tree = self.tree
        db = self.sql3db
        if not self.is_updating:
            self.is_updating = True
            self.disable_buttons()

            # B.2.T.1 Detach previous page items
            if self.shown_giids[0]:
                tree.detach(*self.shown_giids[0])

            # B.2.T.2 Create or reattach next next page group and
            #         file items
            nnpage = self.shown_pages[2] + 1
            nnpage_giids = db.get_group_ids_of_page(nnpage)
            if not set(nnpage_giids).issubset(
                    set(self.populated_giids)):
                # Create next next page items
                self._populate_tree_page_from_sql3db(nnpage)
                evg = 0
            else:
                # Reattach next next page items
                for iid in nnpage_giids:
                    tree.move(iid, "", 'end')  # reattach
                evg = 1

            # B.2.T.3 Update self.shown_pages
            self.shown_pages = [i + 1 for i in self.shown_pages]

            # B.2.T.4 Update self.shown_giids
            self.shown_giids[0] = self.shown_giids[1]
            self.shown_giids[1] = self.shown_giids[2]
            self.shown_giids[2] = nnpage_giids

            # B.2.T.5 Ensure visible group and file items are still
            #         visible
            if visible_giids:
                for vgiid in visible_giids:
                    tree.see(vgiid)
            for vfiid in visible_fiids:
                tree.see(vfiid)

            # B.2.T.6 Generate virtual event
            # Generate virtual event to initiate followup process related to
            # creating or reattaching next page Dupgroups in self.viewport
            # in the Gallery widget.
            if evg == 0:
                tree.event_generate(
                    "<<TreePopulateNextNextPageDone>>",
                    when="tail")
            elif evg == 1:
                tree.event_generate(
                    "<<TreeReattachNextNextPageDone>>",
                    when="tail")

    def reattach_previous_previous_page(self, visible_giids, visible_fiids) \
            -> None:
        tree = self.tree
        db = self.sql3db
        if not self.is_updating:
            self.disable_buttons()
            self.is_updating = True

            # B.2.T.1 Detach next page items.
            if self.shown_giids[2]:
                tree.detach(*self.shown_giids[2])

            # B.2.T.2 Reattach previous previous page group and file
            #         items
            pppage = self.shown_pages[0] - 1
            pppage_giids = db.get_group_ids_of_page(pppage)
            if pppage_giids:
                for iid in pppage_giids[-1:None:-1]:  # in reverse order
                    tree.move(iid, "", 0)  # reattach

            # B.2.T.3 Update self.shown_pages
            self.shown_pages = [i - 1 for i in self.shown_pages]

            # B.2.T.4 Update self.shown_giids
            self.shown_giids[2] = self.shown_giids[1]
            self.shown_giids[1] = self.shown_giids[0]
            self.shown_giids[0] = pppage_giids

            # B.2.T.5 Ensure visible group and file items are
            #         still visible"
            if visible_giids:
                for vgiid in visible_giids[-1:None:-1]:  # in reverse order
                    tree.see(vgiid)
            for vfiid in visible_fiids[-1:None:-1]:  # in reverse order
                tree.see(vfiid)

            # B.2.T.6 Generate virtual event
            # Generate virtual event to initiate followup process related to
            # reattaching previous page Dupgroups in self.viewport in the
            # Gallery widget.
            tree.event_generate(
                "<<TreeReattachPreviousPreviousPageDone>>", when="tail")

    def _dupgroups_page_forward(self) -> None:
        # 1. Destroy previous-previous-page dupgroups
        pppage = self.shown_pages[0] - 1
        pppage_giids = self.sql3db.get_group_ids_of_page(pppage)
        if pppage_giids:
            self._destroy_dupgroups_for_giids(pppage_giids)

        # 2. Create dupgroups of next page
        npage_giids = self.shown_giids[2]
        self._create_dupgroups_for_giids_with_thread_queue(npage_giids)
        # Note: 1. Commands defined hereafter will start immediately after the
        #          thread has started and can complete before the thread_queue
        #          has completed.
        # self._create_dupgroups_for_giids_serially(npage_giids)

    def _dupgroups_page_backward(self) -> None:
        # 1. Destroy next-next-page dupgroups
        nnpage = self.shown_pages[2] + 1
        nnpage_giids = self.sql3db.get_group_ids_of_page(nnpage)
        if nnpage_giids:
            self._destroy_dupgroups_for_giids(nnpage_giids)

        # 2. Create dupgroups of previous page
        ppage_giids = self.shown_giids[0]
        self._create_dupgroups_for_giids_with_thread_queue(ppage_giids)
        # Note: 1. Commands defined hereafter will start immediately after the
        #          thread has started and can complete before or after the
        #          thread_queue has completed.
        # self._create_dupgroups_for_giids_serially(ppage_giids)

    def _destroy_dupgroups_for_giids(self, giids: list[str]) -> None:
        for giid in giids:
            self.dupgroupsframe.dupgroups[giid].destroy()
            del self.dupgroupsframe.dupgroups[giid]
        gc.collect()  # Needed.

    # def _create_dupgroups_for_giids_serially(self, g_iids: list[str]):
    #     """Method to create DupGroup instances inside of self.dupgroupsframe
    #     for a list of group item ids."""
    #     self._start0 = perf_counter()
    #     dgf = self.dupgroupsframe
    #     dgs = self.dupgroupsframe.dupgroups
    #     db = self.sql3db
    #
    #     # 1. Create the DupGroup widget for each giid
    #     f_iids = [db.get_item_ids_of_group(giid) for giid in g_iids]
    #     f_paths = [db.get_full_paths_of_group(giid) for giid in g_iids]
    #     f_selected = [db.get_selected_of_group(giid) for giid in g_iids]
    #     for giid, fiids, fpaths, fselected in zip(g_iids, f_iids, f_paths,
    #                                               f_selected):
    #         dgs[giid] = DupGroup(dgf, giid, fiids, fpaths, fselected,
    #                              with_image=False,
    #                              )
    #         row = int(giid[1:])
    #         dgs[giid].grid(row=row, column=0, sticky='nsew')
    #
    #     end0 = perf_counter()
    #     loadtime = end0 - self._start0
    #     tl, tl_units = timings(loadtime)
    #     print(f'New Dupgroups instances created in {tl:.6f} {tl_units}.')
    #     self.show_1st_visible_treeview_groupitem_in_viewport()
    #     # self.vplabel.lower(self.viewport)
    #     self.is_updating = False
    #     self.enable_buttons()

    def _create_dupgroups_for_giids_with_thread_queue(
            self, g_iids: list[str]) -> None:
        """Method to create DupGroup instances inside of self.dupgroupsframe
        for a list of group item ids."""
        self._start0 = perf_counter()
        dgf = self.dupgroupsframe
        dgs = self.dupgroupsframe.dupgroups
        db = self.sql3db

        # 1. Create the DupGroup widget for each giid
        f_iids = [db.get_item_ids_of_group(giid) for giid in g_iids]
        f_paths = [db.get_full_paths_of_group(giid) for giid in g_iids]
        f_selected = [db.get_selected_of_group(giid) for giid in g_iids]
        for giid, fiids, fpaths, fselected in zip(g_iids, f_iids, f_paths,
                                                  f_selected):
            dgs[giid] = DupGroup(dgf, giid, fiids, fpaths, fselected,
                                 # with_image=True,
                                 with_image=False,
                                 )
            row = int(giid[1:])
            dgs[giid].grid(row=row, column=0, sticky='nsew')

        # 2. Concurrently convert each picture duplicate to a thumbnail and
        #    include into the respective Checkbutton in the DupGroup widgets.
        self._tthread = threading.Thread(
            target=get_thumbnails_concurrently_with_queue,
            args=(g_iids, f_iids, f_paths, self._thumbnails_queue),
            kwargs={"ncpu": os.cpu_count(),
                    "cfe": self._cfe,
                    "exit_event": self._exitevent},
            name="thumbnailthread")
        self._tthread.start()
        self._check_thumbnails_queue()

    def _check_thumbnails_queue(self) -> None:
        duration = 1  # millisecond
        try:
            info = self._thumbnails_queue.get(block=False)
        except queue.Empty:
            # let's try again later
            self.after(duration,
                       lambda: self._check_thumbnails_queue())
        else:
            # Extract info from queue
            match info[0]:
                case "thumbnail":
                    giid, fiid, img = info[1]
                    dgs = self.dupgroupsframe.dupgroups
                    dgs[giid].imf_thumbnails[fiid] = ImageTk.PhotoImage(img)
                    dgs[giid].imf_checkbuttons[fiid]["image"] = \
                        dgs[giid].imf_thumbnails[fiid]
                    self.show_1st_visible_treeview_groupitem_in_viewport()
                    self.after(duration, lambda: self._check_thumbnails_queue())
                case "completed":
                    end0 = perf_counter()
                    loadtime = end0 - self._start0
                    tl, tl_units = timings(loadtime)
                    print(f'New Dupgroups instances created in '
                          f'{tl:.6f} {tl_units}.')
                    self.show_1st_visible_treeview_groupitem_in_viewport()
                    self.vplabel.lower(self.viewport)
                    self.is_updating = False
                    self.enable_buttons()
                    # self.dupgroupsframe.event_generate(
                    #     "<<DupgroupframeUpdated>>", when="tail")

    def show_1st_visible_treeview_groupitem_in_viewport(self) -> None:
        """Method to ensure the Viewport 1st visible DupGroup instance
        correspond to the 1st visible group item in the Treeview.
        """
        dgs = self.dupgroupsframe.dupgroups
        vgiids = self.get_visible_group_iids()
        # self.update_idletasks()
        if vgiids:
            first_tn_y = dgs[vgiids[0]].winfo_y()
        else:
            vfiids = self.get_visible_file_iids()
            fiid0 = vfiids[0]
            giid = fiid0[0:fiid0.index("_")]
            first_tn_y = dgs[giid].winfo_y()
        tnf_height = self.viewport.interior.winfo_reqheight()
        self.viewport.canvas.yview_moveto(first_tn_y / tnf_height)

    def _update_dupgroups_checkvalues(self) -> None:
        """Event handler to update the checkbox of every Checkbutton of every
         DupGroup instances."""
        db = self.sql3db
        dgs = self.dupgroupsframe.dupgroups
        # 1. Get selected and unselected fiids from sql
        sel_fiids = list(db.get_selected().keys())
        unsel_fiids = list(db.get_selected(value=False).keys())

        # 2. Get their corresponding unique giids
        unique_sel_giids = set([i[:i.index("_")] for i in sel_fiids])
        unique_unsel_giids = set([i[:i.index("_")] for i in unsel_fiids])

        # 3. Identify those giids that are shown in the treeview
        shown_giids = [giid for giids in self.shown_giids for giid in
                       giids]
        shown_giids_sel = unique_sel_giids.intersection(set(shown_giids))
        shown_giids_unsel = \
            unique_unsel_giids.intersection(set(shown_giids))

        # 4. Extract those fiids that were ever populated in the treeview
        shown_fiids_sel = [i for i in sel_fiids if i[:i.index("_")] in
                           shown_giids_sel]
        shown_fiids_unsel = [i for i in unsel_fiids if i[:i.index("_")] in
                             shown_giids_unsel]

        # 5. Update the checkvalues of each CheckButton (cb) in all Dupgroup
        #    instances (regardless of whether they are visible or hidden).
        # Selected fiids
        for fiid in shown_fiids_sel:
            giid = fiid[:fiid.index("_")]
            dgs[giid].imf_checkvalues[fiid].set(True)
        # Unselected fiids
        for fiid in shown_fiids_unsel:
            giid = fiid[:fiid.index("_")]
            dgs[giid].imf_checkvalues[fiid].set(False)

    def create_tree_bindings_part_2(self) -> None:
        tree = self.tree
        # 1. Create DupGroup instances in self.dupgroupframe for shown giids
        #    after self.tree is populated for the first time.
        tree.bind("<<TreePopulateDone>>", self._event_populate_viewport)

        # 2. Ensure Viewport 1st visible DupGroup instance correspond to the
        #    1st visible group item in the Treeview.
        tree.bind("<<TreeScrollUpDone>>",
                  self._event_show_1st_visible_treeview_groupitem_in_viewport)
        tree.bind("<<TreeScrollDownDone>>",
                  self._event_show_1st_visible_treeview_groupitem_in_viewport)
        tree.bind("<<TreeStartReached>>",
                  self._event_show_1st_visible_treeview_groupitem_in_viewport)
        tree.bind("<<TreeEndReached>>",
                  self._event_show_1st_visible_treeview_groupitem_in_viewport)

        # 3. Create & delete dupgroups during page transitions
        tree.bind("<<TreePopulateNextNextPageDone>>",
                  self._event_dupgroups_page_forward)
        tree.bind("<<TreeReattachNextNextPageDone>>",
                  self._event_dupgroups_page_forward)
        tree.bind("<<TreeReattachPreviousPreviousPageDone>>",
                  self._event_dupgroups_page_backward)

        # 4. Update the checkboxes of each DupGroup instance whenever one or
        #    more Treeview item is/are toggled.
        tree.bind("<<TreeFileItemsToggled>>",
                  self._event_update_dupgroups_checkvalues)

        # 5. Ensure that clicked file item in the treeview (i.e.self.tree)
        #    moves the corresponding DupGroup instance to the top of the
        #    viewport.
        tree.bind("<<MoveDupGroupToTop>>",
                  self._event_move_dupgroup_to_top_of_viewport)

    def _move_dupgroup_to_top_of_viewport(self) -> None:
        """Event handler to ensure the Viewport 1st visible DupGroup instance
         correspond to the group of the clicked file item in the Treeview."""
        fiid = self.clicked_f_items[0]
        giid = self.sql3db.get_group_id_of_item(fiid)
        try:
            dg_y = self.dupgroupsframe.dupgroups[giid].winfo_y()
        except KeyError:
            if self._after_id_move_dupgroup_to_top_of_viewport:
                self.after_cancel(
                    self._after_id_move_dupgroup_to_top_of_viewport)
            self._after_id_move_dupgroup_to_top_of_viewport = \
                self.after(100, self._move_dupgroup_to_top_of_viewport)
        else:
            dgf_height = self.viewport.interior.winfo_reqheight()
            self.viewport.canvas.yview_moveto(dg_y / dgf_height)

    def _create_dupgroupsframe_bindings(self) -> None:
        # 1. Update the tags of the file item in the Treeview corresponding to
        #    the toggled Checkbutton and ensure the group item and all its
        #    file items are visible in the Treeview.
        self.dupgroupsframe.bind("<<CheckbuttonToggled>>",
                                 self._event_toggle_tree_file_item_appearance)

    def _event_populate_viewport(self, event) -> None:
        self.vplabel.lift(self.viewport)

        def do_task():
            giids = [giid for giids in self.shown_giids for giid in giids]
            self._create_dupgroups_for_giids_with_thread_queue(giids)
            # self._create_dupgroups_for_giids_serially(giids)

        self.after(200,  do_task)

    def _event_reset_viewport(self, event) -> None:
        self.reset_viewport()

    def _event_show_1st_visible_treeview_groupitem_in_viewport(self, event) \
            -> None:
        self.show_1st_visible_treeview_groupitem_in_viewport()

    def _event_dupgroups_page_forward(self, event) -> None:
        self.vplabel.lift(self.viewport)

        if self._after_id_dupgroups_paging:
            self.after_cancel(self._after_id_dupgroups_paging)
        self._after_id_dupgroups_paging = \
            self.after(100, self._dupgroups_page_forward)

    def _event_dupgroups_page_backward(self, event) -> None:
        self.vplabel.lift(self.viewport)

        if self._after_id_dupgroups_paging:
            self.after_cancel(self._after_id_dupgroups_paging)
        self._after_id_dupgroups_paging = \
            self.after(100, self._dupgroups_page_backward)

    def _event_update_dupgroups_checkvalues(self, event) -> None:

        def rerun():
            if self._after_id_update_dupgroups_checkvalues:
                self.after_cancel(self._after_id_update_dupgroups_checkvalues)
            self._after_id_update_dupgroups_checkvalues = \
                self.after(200,
                           lambda:
                           self._event_update_dupgroups_checkvalues(event))

        dg = set(self.dupgroupsframe.dupgroups.keys())
        children = set(event.widget.get_children())
        if self.is_updating:
            rerun()
        elif dg != children:
            rerun()
        else:
            self._update_dupgroups_checkvalues()

    def _event_move_dupgroup_to_top_of_viewport(self, event) -> None:
        """Event handler to ensure the Viewport 1st visible DupGroup instance
         correspond to the group of the clicked file item in the Treeview."""
        self._move_dupgroup_to_top_of_viewport()

    def _event_toggle_tree_file_item_appearance(self, event) -> None:
        tree = self.tree
        db = self.sql3db

        # 1. Get fiid of clicked Checkbutton
        fiid = event.widget.toggled_checkbutton.cget('text')

        # 2. Toggle the fiid's selected value in the sql_database
        db.toggle_selected_of_item(fiid)

        # 3. Update the fiid's appearance/tags in the Treeview
        self.update_tree_file_item_tags(fiid)

        # 4. Ensure all file items similar to fiid and their group item are
        #    visible in the Treeview.
        giid = db.get_group_id_of_item(fiid)
        fiids = db.get_item_ids_of_group(giid)
        for iid in fiids[-1::-1]:
            tree.see(iid)
        tree.see(giid)

        # 5. Update the state of delete button in self.table
        self.update_bn_delete_state()


if __name__ == '__main__':
    from adp.widgets.w_ttkstyle import customise_ttk_widgets_style
    from adp.widgets.w_find import Find

    class App(ttk.Frame):
        def __init__(self, master, **options) -> None:
            self.cfe = pop_kwargs("cfe", ["process", "thread"], options)
            self.layout = pop_kwargs("layout", ["vertical", "horizontal"],
                                     options)
            match self.layout:
                case "vertical": self.orient = "vertical"
                case "horizontal": self.orient = "horizontal"
            self.master = master
            super().__init__(master, **options)

            self._create_widgets()
            self._create_bindings()

        def _create_widgets(self) -> None:
            self.find = Find(self, gallery=True, cfe=self.cfe,
                             layout=self.layout)
            self.find.hide_selected_path()
            self.find.w_pb.pb2.configure(mode="indeterminate")

            self.gallery = Gallery(self, orient=self.orient, cfe=self.cfe)
            self.gallery.set_sdir(self.find.selected_dir)
            self.gallery.set_sql3db(self.find.sqlite3_db)

            self.find.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
            if self.layout in "vertical":
                self.gallery.grid(row=0, column=1, sticky="nsew", padx=(0, 10),
                                  pady=10)
                self.columnconfigure(1, weight=1)
                self.rowconfigure(0, weight=1)
                self.winfo_toplevel().minsize(width=1000, height=600)
            elif self.layout in "horizontal":
                self.gallery.grid(row=1, column=0, sticky="nsew", padx=10,
                                  pady=10)
                self.columnconfigure(0, weight=1)
                self.rowconfigure(1, weight=1)
                self.winfo_toplevel().minsize(width=1200, height=500)

        def _create_bindings(self) -> None:
            self.find.unbind("<<DirectorySelected>>")
            self.find.bind("<<DirectorySelected>>", self.event_reset_app)
            self.find.bind("<<Sqlite3DBPopulated>>",
                           self.gallery.event_populate_tree_the_first_time)
            self.gallery.bn_delete.bind("<<DeletionDone>>", self.event_recheck)

            # # Progressbar during sqlite creation, tree population/updating &
            # # dupgroupsframe population/updating.
            # self.find.bind("<<FindDone>>",
            #                func=self.event_show_indeteminate_pb,
            #                add="+")
            # self.gallery.tree.bind("<<TreePopulateNextNextPageDone>>",
            #                       func=self.event_show_indeteminate_pb,
            #                       add="+")
            #
            # self.gallery.tree.bind("<<TreeReattachNextNextPageDone>>",
            #                       func=self.event_show_indeteminate_pb,
            #                       add="+")
            # self.gallery.tree.bind("<<TreeReattachPreviousPreviousPageDone>>",
            #                       func=self.event_show_indeteminate_pb,
            #                       add="+")
            # self.gallery.dupgroupsframe.bind("<<DupgroupframeUpdated>>",
            #                                  self.event_hide_indeteminate_pb)

        def event_reset_app(self, event) -> None:
            # 1. Reset Gallery, i.e. Table and Viewport
            gallery = self.gallery
            if gallery.tree.get_children():
                gallery.reset_table()
                gallery.reset_viewport()
                gallery.create_tree_bindings_part_2()
            self.after_idle(gallery.set_tree_column0_heading_text,
                            gallery.sdir.get())

            # 2. Enable find button
            self.after_idle(self.find.enable_find_button)

        # def event_show_indeteminate_pb(self, event):
        #     print("event_show_indeteminate_pb")
        #     find = self.find
        #     # find.w_pb.hide()
        #     find.w_pb.show_pb2()
        #     find.w_pb.pb2.start(100)
        #
        # def event_hide_indeteminate_pb(self, event):
        #     print("event_hide_indeteminate_pb")
        #     find = self.find
        #     find.w_pb.pb2.stop()
        #     find.w_pb.hide_pb2()

        def event_recheck(self, event) -> None:
            print(f"\nRecheck {self.find.selected_dir.get()}")
            self.find.reset()
            self.event_reset_app(event)
            self.after_idle(self.find.bn_find.invoke)

        def exit(self) -> None:
            self.find.exit()


    root = tk.Tk()
    root["background"] = BG
    root.title('ANY DUPLICATED PICTURES?')
    root.geometry('1300x600')

    # Commands to create icon
    app_icon = str(CWD) + "/icons/adp/ADP_icon_256.png"
    wm_icon = ImageTk.PhotoImage(file=app_icon)
    wm_icon.image = app_icon
    root.tk.call('wm', 'iconphoto', root, wm_icon)

    s = ttk.Style()
    style = customise_ttk_widgets_style(s)

    # app = App(root, cfe="thread", layout="vertical")
    # app = App(root, cfe="thread", layout="horizontal")
    app = App(root, cfe="process", layout="horizontal")
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
            root.quit()
            root.destroy()


    # Setup root window's shutdown and start it's main events loop
    root.protocol('WM_DELETE_WINDOW', exit_root)

    root.mainloop()
