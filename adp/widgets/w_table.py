# print(f"{__name__}")

# Python modules
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
import platform
from time import perf_counter

# Project modules
from adp.functions import timings
from adp.widgets.constants import DFONT, BFONT, CWD, C0_light, D2_C1, D2_C2, BG
from adp.widgets.w_scrframe import AutoScrollbar
from adp.widgets.w_tools import string_pixel_size

__all__ = ["Table"]
__version__ = '0.1'
__author__ = 'Chia Yan Hon, Julian.'
__copyright__ = "Copyright 2024, Chia Yan Hon, Julian."
__license__ = "Apache License, Version 2.0"

dfont = list(DFONT.values())
bfont = list(BFONT.values())


class Table(ttk.Frame):
    """ This widget consist of a ttk.Treeview with both a vertical and a
    horizontal AutoScrollbar widgets and five ttk.Button widgets below them
    of which two of them are for debugging purposes.

    The treeview displays the sub-filepath, size and creation date of duplicated
    raster images, while the selection status is hidden (it is exposed
    during debugging). The selection and de-selection of a row of data in the
    treeview can be toggled via mouse pointer clicking. Alternatively, the
    selection or de-selection of either the original or copied versions of
    any of the duplicated raster images can be toggled via clicking on the
    respective ttk.Buttons widgets. Finally, the deletion of the selected
    raster image(s) occurs when the clicked 'Delete' button is released.

    IMPORTANT:
    1. This widget is designed to be used with the Find widget.
    2. After instantiating this Table widget, its self.set_sdir() and
       self.set_sql3db() methods need to be used, else the Table widget won't
       work. For example:
        find = Find(root)
        table = Table(root)
        table.set_sdir(find.selected_dir)  # set source/selected directory
        table.set_sql3db(find.sqlite3_db)  # set sqlite3 database
        find.grid(row=0, column=0, sticky="nsew")
        table.grid(row=0, column=1, sticky="nsew")
    3. The treeview is first populated with the first page of data from
       find.sqlite3_db after the find widget generates the
       "<<Sqlite3DBPopulated>>" virtual event or when the clicked `Populate`
       ttk.Button widget is released.
    4. For Tk 8.6 and below, once a tag is created in a Treeview, it cannot
       be deleted. It remains throughout the lifetime of the Treeview. This
       is a memory leak bug and it will only be fixed in Tk 8.7 (see
       https://stackoverflow.com/questions/76689557/deleting-all-items-of-a-ttk-treeview-does-not-delete-or-unconfigure-their-tagnam).
       To avoid this memory leak bug when resetting the Treeview widget,
       the only available option is to destroy and recreate the Treeview widget.

    icon from <a href="https://www.flaticon.com/free-icons/user-interface"
    title="user interface icons"> User interface icons created by Metami
    septiana - Flaticon</a>/


    Generated Virtual Events:

    By self:
    "<<TableResetDone>>" - after resetting self.

    By self.tree:
    "<<TreePopulated>>" - after self.tree is first populated with items.
    "<<TreeScrollUp>>"  - after a series of mousewheel scroll-up events
    "<<TreeScrollDown>>" - after a series of mousewheel scroll-down events
    "<<TreeScrollUpDone>>" - after top of page is not reached.
    "<<TreeScrollDownDone>>" - after bottom of page is not reached.
    "<<TreeStartReached>>" - after top of first page is reached.
    "<<TreeEndReached>>"  - after bottom of last page is reached.
    "<<TreePopulateNextPageDone>>" - after populating next page of self.tree.
    "<<TreeReattachNextPageDone>>"  - after reattaching next page items in
                                      self.tree.
    "<<TreeReattachPreviousPageDone>>" - after reattaching previous page items
                                         in self.tree.
    "<<MoveDupGroupToTop>>" - after toggling the first file item in self.tree
                             that is selected by the mouse pointer and before
                             "<<TreeFileItemsToggled>>".
    "<<TreeFileItemsToggled>>"  - after toggling all file item(s) in self.tree
                                  that are selected by the mouse pointer.

    By self.bn_delete:
    "<<DeletionDone>>" - after the deletion process are completed.
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
                raise TypeError(f"debug={debug} is invalid. It must either be "
                                f"True or False.")
        super().__init__(master, **options)
        self.master = master
        self.sql3db = None
        self.sdir = None
        self._initialise_paging_and_selection_attributes()
        self.tree = None  # widget
        self.xsb = None  # widget
        self.ysb = None  # widget
        self.framebns = None  # widget
        self.bn_originals = None  # widget
        self.bn_copies = None  # widget
        self.bn_delete = None  # widget
        self.bn_populate_tree = None  # widget
        self.bn_reset = None  # widget

        i1 = str(CWD) + "/icons/Flaticon/copy.png"
        i2 = str(CWD) + "/icons/oxygenTeam/delete.png"
        self.icon_duplicates = tk.PhotoImage(file=i1)
        self.icon_delete = tk.PhotoImage(file=i2)
        self.icon_duplicates.image = i1
        self.icon_delete.image = i2

        self._create_widgets()
        self._create_bindings()

    def _initialise_paging_and_selection_attributes(self):
        self.populated = False  # Bool indicates if self.tree is populated
        self.populated_giids = set()
        self.shown_pages = [-1, -1, -1]  # (previous, current, next)
        self.shown_giids = [[], [], []]  # (previous, current, next)
        self.up_after_id = None
        self.down_after_id = None
        self.clicked_f_items = None

    # ---------- Methods ---------
    def set_tree_column0_heading_text(self, text: str):
        """Method to set the text of Treeview heading at column 0."""
        self.tree.heading('#0', text=text)

    def set_sql3db(self, sql3db):
        self.sql3db = sql3db
        # print(f"{self.sql3db=}")

    def set_sdir(self, directory: tk.StringVar):
        """Method to define the directory to search for duplicated photos."""
        self.sdir = directory
        # print(f"{self.sdir=}")
        self.set_tree_column0_heading_text(directory.get())

    def _create_widgets(self):
        """Create a Treeview with vertical and horizontal scrollbars and 2
        buttons each to toggle the selection of original and copies of
        duplicated raster images."""
        self.create_tree_with_scrollbars()
        self.create_buttons()

    def create_tree_with_scrollbars(self):
        self.tree = ttk.Treeview(self, height=10, selectmode='extended',
                                 takefocus=True, columns=("fullpath", "size",
                                                          "created on",
                                                          "selected", "iid"))
        if self.debug:
            self.tree["displaycolumns"] = ["iid", "created on", "size",
                                           "selected"]
        else:
            self.tree["displaycolumns"] = ["iid", "created on", "size"]

        # Setup column & it's headings
        # The width of #0 column will be reconfigured by
        self.tree.column('#0', stretch=False, minwidth=100, width=550,
                         anchor='w')
        self.tree.column('fullpath', stretch=False, anchor='w', width=650)
        self.tree.column('size', stretch=False, anchor='n', width=90)
        self.tree.column('created on', stretch=False, anchor='n', width=140)
        self.tree.column('selected', stretch=False, anchor='n', width=80)
        self.tree.column('iid', stretch=False, anchor='n', width=60)

        self.tree.heading('#0', text="", anchor='w')
        self.tree.heading('fullpath', text='Full Path', anchor='w')
        self.tree.heading('size', text='File Size', anchor='center')
        self.tree.heading('created on', text='Created On', anchor='center')
        self.tree.heading('selected', text='Selected', anchor='center')
        self.tree.heading('iid', text='Item id', anchor='center')
        # #0, #01, #02 denotes the 0, 1st, 2nd columns

        self.ysb = AutoScrollbar(self, orient='vertical',
                                 command=self.tree.yview)
        self.xsb = AutoScrollbar(self, orient='horizontal',
                                 command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.ysb.set,
                            xscrollcommand=self.xsb.set)

        # Position treeview, scrollbars in self
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.tree.grid(row=0, column=0, sticky='nsew')
        self.ysb.grid(row=0, column=1, sticky='ns')
        self.xsb.grid(row=1, column=0, sticky='ew')

    def create_buttons(self):

        def o_handler(widget=self, i="Original"):
            return widget._bn_toggle_dtype(i)

        def c_handler(widget=self, i="Copy"):
            return widget._bn_toggle_dtype(i)

        # A row of buttons
        self.framebns = ttk.Frame(self, style='Framebns.TFrame')
        self.bn_originals = ttk.Button(self.framebns, text="Originals",
                                       command=o_handler,)
        self.bn_copies = ttk.Button(self.framebns, text="Copies",
                                    command=c_handler,)
        self.bn_delete = ttk.Button(self.framebns, text="Delete",
                                    command=self._delete_button_invoked,
                                    )
        self.disable_buttons()

        self.framebns.grid(row=2, column=0, columnspan=2, sticky='ew',)

        # Position buttons in framebns
        self.framebns.columnconfigure(0, weight=1)
        self.framebns.columnconfigure(1, weight=1)
        self.framebns.columnconfigure(6, weight=1)
        self.bn_originals.grid(row=0, column=0, sticky="nsew", padx=(10, 5),
                               pady=5)
        self.bn_copies.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.bn_delete.grid(row=0, column=6, sticky="nsew", padx=(5, 10),
                            pady=5)

        if self.debug:
            self.bn_populate_tree = ttk.Button(
                self.framebns, text="Populate SQL & Tree",
                command=self.populate_tree_the_first_time)
            self.bn_populate_tree.grid(row=0, column=3, padx=5, pady=5,)

            self.bn_reset = ttk.Button(
                self.framebns, text="Reset", command=self.reset_table)
            self.bn_reset.grid(row=0, column=4, padx=5, pady=5,)
            self.bn_reset.state(("disabled",))

    def disable_buttons(self):
        """Method to disable buttons."""
        self.bn_originals.state(['disabled'])
        self.bn_copies.state(['disabled'])
        self.bn_delete.state(['disabled'])

    def enable_buttons(self):
        """Method to enable buttons"""
        self.bn_originals.state(['!disabled'])
        self.bn_copies.state(['!disabled'])
        # self.bn_delete.state(['!disabled'])

    def get_tree_displaycolumns_headings_text(self, icon_column=True):
        """Method to return a generator of the displayed columns heading text
        of the self.tree widget."""
        displaycolumns = list(self.tree["displaycolumns"])
        if icon_column:
            displaycolumns.insert(0, "#0")
        texts = (self.tree.heading(i)["text"] for i in displaycolumns)
        return texts

    def populate_tree_the_first_time(self):
        """Event handler to populate self.tree for the first time."""
        # print("\ndef populate_tree_the_first_time(self):")

        # 1. Update self.shown_pages
        # self.shown_pages = [-1, -1, -1]  is default
        all_pages = self.sql3db.get_all_page_numbers()
        if all_pages:
            if len(all_pages) == 1:  # only 1 page
                self.shown_pages = [-1, 0, -1]
            else:  # more than 1 page
                self.shown_pages = [-1, 0, 1]
        spage = self.shown_pages  # (previous, current, next)
        # print(f"{self.shown_pages=}")

        # 2. When to populate tree for the first time
        if spage[1] == 0:
            # 2.1. Populate tree with current page
            t1 = perf_counter()
            self._populate_tree_page_from_sql3db(spage[1])  # current page
            self.populated = True

            # 2.2. Populate tree with next page
            if spage[2] > 0:
                self._populate_tree_page_from_sql3db(spage[2])  # next page
            t2 = perf_counter()
            loadtime = t2 - t1
            tl, tl_units = timings(loadtime)
            print(f'Populated Table in {tl:.6f} {tl_units}.')

            # 2.3. Update self.shown_giids
            for n, page in enumerate(self.shown_pages):
                if page >= 0:
                    self.shown_giids[n] = self.sql3db.get_group_ids_of_page(page)
                else:
                    self.shown_giids[n] = []
                # print(f"self.shown_giids[{n}] = {self.shown_giids[n]}")

            # 2.4. Generate virtual event immediately
            # print("<<TreePopulatedFirstTimeDone>>")
            self.tree.event_generate("<<TreePopulatedFirstTimeDone>>")

            # 2.5. Set state of buttons
            self.enable_buttons()
            if isinstance(self.bn_populate_tree, ttk.Button):
                self.bn_populate_tree.state(("disabled",))
            if isinstance(self.bn_reset, ttk.Button):
                self.bn_reset.state(("!disabled",))
            self.tree.update_idletasks()

    def _populate_tree_page_from_sql3db(self, page: int):
        """Method to populate treeview with info from sql3db. Arguments
        'start' and 'end' are the first and last indexes of the duplicate
        groups that are to be considered while keyword argument `step` is their
        increment."""
        # print(f"\ndef _populate_tree_page_from_sql3db(self, page: int):")
        tree = self.tree
        db = self.sql3db

        # 1. Initialise width of every displayed column of the tree
        headings = tuple(self.get_tree_displaycolumns_headings_text())
        # print(f"{headings=}")
        wpad = 20
        cols_maxwidth = [string_pixel_size(i, **BFONT)[0] + wpad for i in
                         headings]
        # print(f"{cols_maxwidth=}")

        # 2. Create every group and file items of the tree
        """Each row of data in db contains the following columns: 
        sn, item_id, group_id, hashhex, full_path, child_path, create_on,
        file_size, selected
        """
        g_iids = db.get_group_ids_of_page(page)
        for g_iid in g_iids:
            # Insert Group Nodes
            group = db.get_group_items(g_iid)
            # print(f"{group=}")
            g_hashhex = group[0][3]
            g_values = (g_hashhex,)
            # tree.tag_configure(g_iid, foreground=D2_C1, font=bfont)
            tree.tag_configure(g_iid, foreground=C0_light, font=bfont)
            tree.insert("", "end", iid=g_iid, image=self.icon_duplicates,
                        open=True, tags=[g_iid, 'Duplicates Group'],
                        text=f"Duplicates Group {g_iid[1:]}", values=g_values)

            for mm, row in enumerate(group):
                # Insert File Nodes (children of each Group Node)
                f_iid = row[1]
                f_fullpath = row[4]
                f_childpath = row[5]
                f_text = f_childpath
                f_ctime = row[6]
                f_size = row[7]
                if row[8]:
                    f_selected = True
                    tree.tag_configure(f_iid, foreground="red",
                                       image=self.icon_delete)
                    if mm == 0:
                        f_tags = [f_iid, 'File', "Original", "Selected"]
                    else:
                        f_tags = [f_iid, 'File', "Copy", "Selected"]
                else:
                    f_selected = False
                    if mm == 0:
                        f_tags = [f_iid, 'File', "Original", "Not Selected"]
                        self.tree.tag_configure(f_iid, foreground=D2_C1,
                                                image="")
                    else:
                        f_tags = [f_iid, 'File', "Copy", "Not Selected"]
                        self.tree.tag_configure(f_iid, foreground=D2_C2,
                                                image="")
                f_values = (f_fullpath, f_size, f_ctime, f_selected, f_iid)
                # "fullpath", "size", "created on", "selected", "iid"
                tree.insert(g_iid, "end", iid=f_iid, tags=f_tags, text=f_text,
                            values=f_values)

                # Update columns max width variables
                row_values = [f_childpath, f_iid, f_ctime, f_size]
                # print(f"{row_values=}")
                row_maxwidths = [string_pixel_size(i, **DFONT)[0] + wpad
                                 for i in row_values]
                leftpad = 60  # pixels
                row_maxwidths[0] += leftpad
                for nn, (rmw, cmw) in enumerate(
                        zip(row_maxwidths, cols_maxwidth)):
                    # print(nn, rmw, cmw)
                    if rmw > cmw:
                        cols_maxwidth[nn] = rmw
                # print(f"{cols_maxwidth=}")

        # 3. Reconfigure the width of column #0 to fit all text
        tree.column('#0', width=cols_maxwidth[0])
        tree.column('iid', width=cols_maxwidth[1])
        tree.column('created on', width=cols_maxwidth[2])
        tree.column('size', width=cols_maxwidth[3])

        # 4. Update self.populated_giids
        self.populated_giids.update(g_iids)

    def reset_table(self):
        # 1. Reinitialise these attributes
        self._initialise_paging_and_selection_attributes()

        # 2. Destroy and recreate tree and scrollbars
        self.tree.destroy()  # widget
        self.ysb.destroy()
        self.xsb.destroy()
        self.create_tree_with_scrollbars()

        # 3. Reset buttons appearance
        self.disable_buttons()
        if isinstance(self.bn_populate_tree, ttk.Button):
            self.bn_populate_tree.state(("!disabled",))
        if isinstance(self.bn_reset, ttk.Button):
            self.bn_reset.state(("disabled",))

        # 4. Recreate events bindings
        self._create_bindings()

        # 5. Generate virtual event to indicate that table reset is done.
        # print("<<TableResetDone>>")
        self.event_generate("<<TableResetDone>>", when="tail")

    def get_visible_group_iids(self):
        """Method to get the idd of visible toplevel items in the Treeview"""
        # print("\ndef get_visible_group_iids(self)")
        tree = self.tree
        self.update_idletasks()
        # pcn_giids = tree.get_children()
        pcn_giids = [j for i in self.shown_giids for j in i]
        # print(f"{pcn_giids=}")
        visible_pcn_giids = [iid for iid in pcn_giids
                             if isinstance(tree.bbox(iid), tuple)]
        # print(f"{visible_pcn_giids=}")
        # print(f"{self.xsb.winfo_ismapped()=}")
        if visible_pcn_giids:
            if self.xsb.winfo_ismapped():
                xsb_y = self.xsb.winfo_y()
                _, y, _, h = tree.bbox(visible_pcn_giids[-1])
                last_giid_btm = y + h
                # print(f"{last_giid_btm=} {xsb_y=}")
                if last_giid_btm > xsb_y:
                    visible_pcn_giids.pop()
            # print(f"{visible_pcn_giids=}")
            return visible_pcn_giids
        else:
            return None

    def get_visible_file_iids(self):
        """Method to get the idd of visible toplevel items in the Treeview"""
        # print("\ndef get_visible_file_iids(self)")
        tree = self.tree
        db = self.sql3db
        self.update_idletasks()
        pcn_giids = [j for i in self.shown_giids for j in i]
        pcn_fiids = []
        for giid in pcn_giids:
            pcn_fiids.extend(db.get_item_ids_of_group(giid))
        # print(f"{len(pcn_giids)=} {pcn_giids=}")
        visible_pcn_fiids = [iid for iid in pcn_fiids
                             if isinstance(tree.bbox(iid), tuple)]
        # print(f"{visible_pcn_fiids=}")
        # print(f"{self.xsb.winfo_ismapped()=}")
        if visible_pcn_fiids:
            if self.xsb.winfo_ismapped():
                xsb_y = self.xsb.winfo_y()
                _, y, _, h = tree.bbox(visible_pcn_fiids[-1])
                last_fiid_btm = y + h
                # print(f"{last_fiid_btm=} {xsb_y=}")
                if last_fiid_btm > xsb_y:
                    visible_pcn_fiids.pop()
            # print(f"{visible_pcn_giids=}")
            return visible_pcn_fiids
        else:
            return None

    def _bn_toggle_dtype(self, dtype):
        """Method to toggle the selection of items with dtype having the value
        of either 'Original' or 'Copy'.
        1. Toggle the selected values in the sql-databse.
        2. Update the appearances of file items in the treeview current page,
           i.e. attached items are updated.
        3. Update the appearances of all detached items.
        4. Update state of delete button
        5. Generate virtual event <<TreeFileItemsToggled>>
        """
        # print(f"\ndef _bn_toggle_dtype(self):")
        if dtype not in ["Original", "Copy"]:
            raise ValueError(f"The value of 'dtype' must either be 'Original'"
                             f" or 'Copy'. {dtype} is invalid.")
        tree = self.tree
        db = self.sql3db

        def update_column_and_tag_values(fids: list, selected_values: list):
            """Function to toggle the appearances of fidds in the Treeview
            widget."""
            for fid, sel in zip(fids, selected_values):
                fid_tags = list(tree.item(fid, option='tags'))
                # print(f"{fid=} {sel=} {type(sel)=}{fid_tags=}")
                if sel == 0:
                    # print("sel == 0")
                    tree.set(fid, column="selected", value="False")
                    fid_tags[3] = 'Not Selected'
                    if dtype in ["Original"]:
                        tree.tag_configure(fid, foreground=D2_C1, image='')
                    else:
                        tree.tag_configure(fid, foreground=D2_C2, image='')
                else:
                    # print("else")
                    tree.set(fid, column="selected", value="True")
                    fid_tags[3] = 'Selected'
                    tree.tag_configure(fid, foreground="red",
                                       image=self.icon_delete)
                tree.item(fid, tags=fid_tags)  # Update tags

        # 1. Toggle the values in the selected column of the SQL_database
        #    Note: Toggling only occurs when the selected values are all 0 or
        #          are all 1. If this situation is not the case, then all
        #          selected values will be set to 0.
        f_iids = db.get_selected_of_dtype(dtype)
        # print(f"Bef: {len(f_iids)=} {f_iids=}")
        if all(f_iids) or not any(f_iids):
            db.toggle_all_selected_of_dtype(dtype)
        else:
            # Set all value to True
            db.set_selected_of_dtype(dtype, "1")
        # f_iids = db.get_selected_of_dtype(dtype)
        # print(f"Aft: {len(f_iids)=} {f_iids=}")

        # 2. Set the corresponding appearances of the attached items in the
        #    Treeview widget.
        #    Note: The Treeview widget only shows 3 pages of the sql_database
        #          and not the entire sql_database. Namely, the previous,
        #          current and next pages stored in self.shown_pages.
        # 2.1 Get the iids of all dtype photos attached to the Treeview widget
        attached_iids = tree.tag_has(dtype)
        # print(f"{len(attached_iids)=} {attached_iids=}")
        # 2.2. Get their selected values from the sql-database
        aselected = [db.get_selected_of_item(iid) for iid in attached_iids]
        # print(f"{aselected=}")
        # 2.3. Update their appearances in the Treeview widget
        update_column_and_tag_values(attached_iids, aselected)

        # 3. Set the corresponding appearances of the detached items of the
        #    Treeview widget.
        # 3.1 Get detached group items
        shown_giids = [giid for giids in self.shown_giids for giid in giids]
        # print(f"{shown_giids=}")
        detached_giids = list(set(self.populated_giids).difference(shown_giids))
        # print(f"{detached_giids=}")
        # 3.2 Get their children
        detached_fiids = []
        detached_dtype_fiids = []
        for dgiid in detached_giids:
            fiids = tree.get_children(dgiid)
            detached_fiids.extend(fiids)
            for fiid in fiids:
                if db.get_item(fiid)[9] in dtype:
                    detached_dtype_fiids.append(fiid)
        # print(f"{detached_fiids=}")
        # print(f"{detached_dtype_fiids=}")
        # 3.3 Get the selected values of the detached items from the
        #      sql-database
        d_sel_values = [db.get_selected_of_item(iid) for iid in
                        detached_dtype_fiids]
        # print(f"{d_sel_values=}")
        # 3.4 Update their appearances in the Treeview widget
        update_column_and_tag_values(detached_dtype_fiids, d_sel_values)

        # 4. Update state of delete button
        self.update_bn_delete_state()

        # 5. Generate virtual event <<TreeFileItemsToggled>>
        # print(f"<<TreeFileItemsToggled>>")
        tree.event_generate("<<TreeFileItemsToggled>>", when="now")

    def update_bn_delete_state(self):
        # print(f"\ndef update_bn_delete_state(self):")
        # print(f"{self.tree.tag_has('Selected')=}")
        if not self.tree.tag_has('Selected'):
            self.bn_delete.state(["disabled"])
        else:
            self.bn_delete.state(["!disabled"])

    def _delete_button_invoked(self):
        """Callback to delete the selected photo files."""
        # print(f"\ndef _delete_button_invoked(self):")

        title = "DELETE SELECTED PHOTOS!"
        msg = f"\nPermanent Deletion!!!   \n\n     To Proceed?\n"
        mbox = messagebox.askokcancel(title, msg, icon="warning")

        # 1.Check whether deletion is to be executed.
        if not mbox:
            # print("Do nothing")
            return None

        # 2. Disable the Buttons "Originals" and "Copies".
        self.disable_buttons()
        if self.debug:
            self.bn_reset.state(["disabled"])

        # 3. Get selected files from sql_database
        selected = self.sql3db.get_fiid_giid_fpath_of_selected()
        # print(f"{selected=}")

        # 4. Delete the selected photo files
        # for fiid, (giid, fpath) in selected.items():
        #     fpath = Path(fpath)
        #     fpath.unlink()
        print(f"*** {len(selected)} PHOTOS DELETED! ***")

        # 5. Generate virtual event to indicate deletion is done.
        # print(f"<<DeletionDone>>")
        self.bn_delete.event_generate("<<DeletionDone>>", when="tail")

    def _create_bindings(self):
        tree = self.tree
        ysb = self.ysb
        xsb = self.xsb

        # Control vertical scrolling movement of self.tree and self.ysb due to
        # mousewheel.
        if platform.system() in ["Linux"]:
            tree.bind('<Button-4>', self._event_schedule_scroll_up)
            tree.bind('<Button-5>', self._event_schedule_scroll_down)
            ysb.bind('<Button-4>', self._event_schedule_scroll_up)
            ysb.bind('<Button-5>', self._event_schedule_scroll_down)
        # elif platform.system() in ["Windows"]:
        #     tree.bind("<MouseWheel>",
        #               tree.yview_scroll(int(-1 * (self.ysb.delta / 120)),
        #                                 "units"))
        #     ysb.bind("<MouseWheel>",
        #              tree.yview_scroll(int(-1 * (self.ysb.delta / 120)),
        #                                "units"))

        # Control how self.tree scrolls to next page and previous page
        tree.bind("<<TreeScrollDown>>", self._event_show_next_next_page)
        tree.bind("<<TreeScrollUp>>", self._event_show_previous_previous_page)

        # Control horizontal scrolling movement of self.xsb due to mousewheel
        xsb.bind("<<AutoScrollbarOn>>", self._event_bind_xsb)
        xsb.bind("<<AutoScrollbarOff>>", self._event_unbind_xsb)

        # 1. Use ButtonRelease-1 to select/deselect one or more rows in the
        #    Treeview
        tree.tag_bind('File', sequence='<ButtonRelease-1>',
                      callback=self._event_b1_release_to_toggle_selection)

    def _event_reset_table(self, event):
        self.reset_table()

    def event_populate_tree_the_first_time(self, event):
        self.populate_tree_the_first_time()

    def _event_schedule_scroll_down(self, event):
        """Event handler to generate the last known '<<TreeScrollDown>>'
        virtual event from a stream of '<<TreeScrollDown>>' virtual events."""
        if self.populated:
            if self.down_after_id:
                self.after_cancel(self.down_after_id)
            # print(f"<<TreeScrollDown>>")
            self.down_after_id = self.after(700, self.tree.event_generate,
                                            "<<TreeScrollDown>>")
        else:
            return None

    def _event_schedule_scroll_up(self, event):
        """Event handler to generate the last known '<<TreeScrollUp>>'
        virtual event from a stream of '<<TreeScrollUp>>' virtual events."""
        if self.populated:
            if self.up_after_id:
                self.after_cancel(self.up_after_id)
            # print(f"<<TreeScrollUp>>")
            self.up_after_id = self.after(700, self.tree.event_generate,
                                          "<<TreeScrollUp>>")
        else:
            return None

    def _event_show_next_next_page(self, event):
        # print(f"\ndef _event_show_next_next_page(self, event):")
        tree = self.tree
        db = self.sql3db
        ysb = self.ysb

        # 1. Exit event handler if tree is unpopulated
        all_pages = db.get_all_page_numbers()
        # print(f"{all_pages=}")
        # print(f"{self.populated=}")
        if not self.populated or not all_pages:
            # print("self.tree is unpopulated: Do nothing")
            return None

        # 2. Get visible giids and fiids
        visible_giids = self.get_visible_group_iids()
        visible_fiids = self.get_visible_file_iids()
        # print(f"{visible_giids=}")
        # print(f"{visible_fiids=}")

        # 3. Get coordinate of the scrollbar sash
        _, ysb_btm = ysb.get()  # 0.0 to 1.0 values denote top to bottom
        # print(f"{ysb_btm=}")

        if len(all_pages) == 1:  # If only 1 page
            # print(f"If only 1 page")
            if ysb_btm == 1.0 :  # A.1. At last page bottom
                # print("No next page: <<TreeEndReached>>")
                # print(f"{self.shown_pages=}")
                # for i in self.shown_giids:
                    # print(i)
                tree.event_generate("<<TreeEndReached>>", when="tail")
            else:  # A.2 Not at last page bottom
                # Generate virtual event to trigger a followup process to ensure
                # the Dupgroup of the first visible group item of the Treeview
                # is at the top of the self.viewport in the Gallery widget.
                # print(f"<<TreeScrollDownDone>>")
                tree.event_generate("<<TreeScrollDownDone>>", when="tail")

        else:
            # print(f"If more than 1 page")
            if self.shown_pages[2] == all_pages[-1]:  # A. Next page is last page
                # print(f"Next page is last page")
                if ysb_btm == 1.0 :  # A.1. At last page bottom
                    # print("No next page: <<TreeEndReached>>")
                    # print(f"{self.shown_pages=}")
                    # for i in self.shown_giids:
                    #     print(i)
                    tree.event_generate("<<TreeEndReached>>", when="tail")
                else:  # A.2 Not at last page bottom
                    # Generate virtual event to trigger a followup process to ensure
                    # the Dupgroup of the first visible group item of the Treeview
                    # is at the top of the self.viewport in the Gallery widget.
                    # print(f"<<TreeScrollDownDone>>")
                    tree.event_generate("<<TreeScrollDownDone>>", when="tail")

            else:  # B. Next page isn't last page
                # print(f"Next page is last page")
                # B.1 Get File items id of next page
                npage_fiids = []
                for giid in self.shown_giids[2]:
                    npage_fiids.extend(db.get_item_ids_of_group(giid))
                # print(f"{npage_fiids=}")

                # B.2 Determine whether any visible group and file items belongs
                #     to the next page
                vg_in_npage = any([giid in self.shown_giids[2] for giid in
                                   visible_giids])
                vf_in_npage = any([fiid in npage_fiids for fiid in visible_fiids])
                # print(f"{vg_in_npage=}")
                # print(f"{vf_in_npage=}")

                if vg_in_npage and vf_in_npage:
                    # print(f"# B.2.T Next page group and file items are visible.")

                    if self.shown_giids[0]:
                        # print(f"# B.2.T.1 Detach previous page items.")
                        tree.detach(*self.shown_giids[0])

                    # print(f"B.2.T.2 Create or reattach next next page group and file items")
                    nnpage = self.shown_pages[2] + 1
                    nnpage_giids = db.get_group_ids_of_page(nnpage)
                    # print(f"{nnpage=} {nnpage_giids=}")
                    if not set(nnpage_giids).issubset(set(self.populated_giids)):
                        # print(f"# Create next next page items")
                        self._populate_tree_page_from_sql3db(nnpage)
                        evg = 0
                    else:
                        # print(f"# Reattach next next page items")
                        # for iid in nnpage_giids[-1:None:-1]:  # in reverse order
                        for iid in nnpage_giids:
                            tree.move(iid, "", 'end')  # reattach
                        evg = 1

                    # print(f"# B.2.T.3 Update self.shown_pages")
                    self.shown_pages = [i+1 for i in self.shown_pages]
                    # print(f"Aft {self.shown_pages=}")

                    # print(f"# B.2.T.4 Update self.shown_giids")
                    self.shown_giids[0] = self.shown_giids[1]
                    self.shown_giids[1] = self.shown_giids[2]
                    self.shown_giids[2] = nnpage_giids
                    # for i in self.shown_giids:
                    #     print(i)

                    # print(f"# B.2.T.5 Ensure visible group and file items are still visible")
                    for vgiid in visible_giids:
                        tree.see(vgiid)
                    for vfiid in visible_fiids:
                        tree.see(vfiid)

                    # print(f"# B.2.T.6 Generate virtual event")
                    # Generate virtual event to initiate followup process related to
                    # creating or reattaching next page Dupgroups in self.viewport
                    # in the Gallery widget.
                    if evg == 0:
                        # print(f"<<TreePopulateNextNextPageDone>>")
                        tree.event_generate("<<TreePopulateNextNextPageDone>>",
                                            when="tail")
                    elif evg == 1:
                        # print(f"<<TreeReattachNextNextPageDone>>")
                        tree.event_generate("<<TreeReattachNextNextPageDone>>",
                                            when="tail")
                else:
                    # print(f"# B.2.F Next page group and file items aren't visible.")
                    # Generate virtual event to trigger a followup process to ensure
                    # the Dupgroup of the first visible group item of the Treeview
                    # is at the top of the self.viewport in the Gallery widget.
                    # print(f"<<TreeScrollDownDone>>")
                    tree.event_generate("<<TreeScrollDownDone>>", when="tail")

    def _event_show_previous_previous_page(self, event):
        # print(f"\ndef _event_show_previous_previous_page(self, event):")
        tree = self.tree
        db = self.sql3db
        ysb = self.ysb

        # 1. Exit event handler if tree is unpopulated
        all_pages = db.get_all_page_numbers()
        # print(f"{all_pages=}")
        # print(f"{self.populated=}")
        if not self.populated or not all_pages:
            # print("self.tree is unpopulated: Do nothing")
            return

        # 2. Get visible giids and fiids
        visible_giids = self.get_visible_group_iids()
        visible_fiids = self.get_visible_file_iids()
        # print(f"{visible_giids=}")
        # print(f"{visible_fiids=}")

        # 3 Get coordinate of the scrollbar sash
        ysb_top, _ = ysb.get()  # 0.0 to 1.0 values denote top to bottom
        # print(f"{ysb_top=}")

        if len(all_pages) == 1:  # If only 1 page
            # print(f"If only 1 page")
            if ysb_top == 0.0:  # A.1. At first page top
                # print("No previous page: <<TreeStartReached>>")
                # print(f"{self.shown_pages=}")
                # for i in self.shown_giids:
                #     print(i)
                tree.event_generate("<<TreeStartReached>>", when="tail")
            else:  # A.2 Not at first page top
                # Generate virtual event to trigger a followup process to ensure
                # the Dupgroup of the first visible group item of the Treeview
                # is at the top of the self.viewport in the Gallery widget.
                # print(f"<<TreeScrollUpDone>>")
                tree.event_generate("<<TreeScrollUpDone>>", when="tail")
        else:
            if self.shown_pages[0] == all_pages[0]:  # A. Previous page is last page
                if ysb_top == 0.0:  # A.1. At first page top
                    # print("No previous page: <<TreeStartReached>>")
                    # print(f"{self.shown_pages=}")
                    # for i in self.shown_giids:
                    #     print(i)
                    tree.event_generate("<<TreeStartReached>>", when="tail")
                else:  # A.2 Not at first page top
                    # Generate virtual event to trigger a followup process to ensure
                    # the Dupgroup of the first visible group item of the Treeview
                    # is at the top of the self.viewport in the Gallery widget.
                    # print(f"<<TreeScrollUpDone>>")
                    tree.event_generate("<<TreeScrollUpDone>>", when="tail")
            else:  # B. Previous page isn't first page
                # B.1 Get File items id of previous page
                ppage_fiids = []  # previous page fiids
                for giid in self.shown_giids[0]:
                    ppage_fiids.extend(db.get_item_ids_of_group(giid))
                # print(f"{ppage_fiids=}")

                # B.2 Determine whether any visible group and file items belongs
                #     to the previous page
                vg_in_ppage = any(
                    [giid in self.shown_giids[0] for giid in visible_giids])
                vf_in_ppage = any([fiid in ppage_fiids for fiid in visible_fiids])
                # print(f"{vg_in_ppage=}")
                # print(f"{vf_in_ppage=}")

                if vg_in_ppage and vf_in_ppage:
                    # print(f"# B.2.T Previous page group and file items are visible.")

                    if self.shown_giids[2]:
                        # print(f"# B.2.T.1 Detach next page items.")
                        tree.detach(*self.shown_giids[2])

                    # print(f"B.2.T.2 Reattach previous previous page group and file "
                    #       f"items")
                    pppage = self.shown_pages[0] - 1
                    pppage_giids = db.get_group_ids_of_page(pppage)
                    # print(f"{pppage=} {pppage_giids=}")
                    if pppage_giids:
                        for iid in pppage_giids[-1:None:-1]:  # in reverse order
                            tree.move(iid, "", 0)  # reattach

                    # print(f"# B.2.T.3 Update self.shown_pages")
                    self.shown_pages = [i - 1 for i in self.shown_pages]
                    # print(f"Aft {self.shown_pages=}")

                    # print(f"# B.2.T.4 Update self.shown_giids")
                    self.shown_giids[2] = self.shown_giids[1]
                    self.shown_giids[1] = self.shown_giids[0]
                    self.shown_giids[0] = pppage_giids
                    # for i in self.shown_giids:
                    #     print(i)

                    # print(f"# B.2.T.5 Ensure visible group and file items are still visible")
                    for vgiid in visible_giids[-1:None:-1]:  # in reverse order
                        tree.see(vgiid)
                    for vfiid in visible_fiids[-1:None:-1]:  # in reverse order
                        tree.see(vfiid)

                    # print(f"# B.2.T.6 Generate virtual event")
                    # Generate virtual event to initiate followup process related to
                    # reattaching previous page Dupgroups in self.viewport in the
                    # Gallery widget.
                    # print(f"<<TreeReattachPreviousPreviousPageDone>>")
                    tree.event_generate("<<TreeReattachPreviousPreviousPageDone>>",
                                        when="tail")
                else:
                    # print(f"# B.2.F Next page group and file items aren't visible.")
                    # Generate virtual event to trigger a followup process to ensure
                    # the Dupgroup of the first visible group item of the Treeview
                    # is at the top of the self.viewport in the Gallery widget.
                    # print(f"<<TreeScrollUpDone>>")
                    tree.event_generate("<<TreeScrollUpDone>>", when="tail")

    def _event_bind_xsb(self, event):
        if platform.system() in ["Linux"]:
            event.widget.bind('<Enter>',
                              self._event_bind_xsb_to_mousewheel_linuxos)
            event.widget.bind('<Leave>',
                              self._event_unbind_xsb_from_mousewheel_linuxos)
        elif platform.system() in ["Windows"]:
            event.widget.bind('<Enter>',
                              self._event_bind_xsb_to_mousewheel_winos)
            event.widget.bind('<Leave>',
                              self._event_unbind_xsb_from_mousewheel_winos)

    def _event_unbind_xsb(self, event):
        event.widget.unbind('<Enter>')
        event.widget.unbind('<Leave>')

    def _event_bind_xsb_to_mousewheel_linuxos(self, event):
        def tree_scroll_left(e):
            self.tree.xview_scroll(100, 'units')

        def tree_scroll_right(e):
            self.tree.xview_scroll(-100, 'units')

        event.widget.bind('<Button-4>', tree_scroll_left)
        event.widget.bind('<Button-5>', tree_scroll_right)

    def _event_unbind_xsb_from_mousewheel_linuxos(self, event):
        event.widget.unbind("<Button-4>")
        event.widget.unbind("<Button-5>")

    def _event_bind_xsb_to_mousewheel_winos(self, event):
        event.widget.bind("<MouseWheel>",
                          self.tree.xview_scroll(
                              int(-1 * (event.delta / 120)), "units")
                          )

    def _event_unbind_xsb_from_mousewheel_winos(self, event):
        event.widget.unbind("<MouseWheel>")

    def _event_b1_release_to_toggle_selection(self, event):
        """Method to toggle the selection of one or more file items by
        mouse clicking in the treeview. This method must be bound to treeview
        fields with the tagname called 'File' for it to work correctly.
        Note: the 'selected' value in the self.sql3db will also be toggled."""
        # print('\n_event_b1_release_to_toggle_selection(self, event)')

        # 1. If widget_under_pointer != event.widget
        widget_under_pointer = event.widget.winfo_containing(event.x_root,
                                                             event.y_root)
        if widget_under_pointer != event.widget:
            # print("Do Nothing")
            return None

        # 2. If widget_under_pointer == event.widget
        tree = self.tree
        db = self.sql3db

        # 2.1. Get id of only selected file item(s)
        self.clicked_f_items = [i for i in tree.selection() if "F" in i]
        # print(f"{self.clicked_f_items=}")

        # 2.2. Toggle the "selected" column value, color and the 5th tag value
        #      of these f_items.
        for n, fiid in enumerate(self.clicked_f_items):

                # print(f"Bef.: {db.get_selected_of_item(fiid)=}")

                # 1.Toggle fiid  "selected" column value in sql_database
                db.toggle_selected_of_item(fiid)

                # 2.Update the Treeview tags of a given file item id (fiid)
                self.update_file_item_tags(fiid)
                # print(f"Aft.: {db.get_selected_of_item(fiid)=}")

                # 3. Generate virtual event to allow immediate follow-up action
                if n == 0:
                    # print(f"<<MoveDupGroupToTop>>")
                    tree.event_generate("<<MoveDupGroupToTop>>")

        # 2.3. Update state of delete button
        self.update_bn_delete_state()

        # 2.4. Generate virtual event <<TreeFileItemsToggled>>
        # print(f"<<TreeFileItemsToggled>>")
        tree.event_generate("<<TreeFileItemsToggled>>")

    def update_file_item_tags(self, fiid):
        """Method to update the Treeview tags of a given file item id (fiid)"""
        tree = self.tree
        db = self.sql3db

        # 1. Get the fiid's "selected" column value
        selected = db.get_selected_of_item(fiid)
        # print(f"{selected=}")

        # 2. Get fiid's Treeview tags
        f_item_tags = list(tree.item(fiid, option='tags'))  # tree f_item tag
        # print(f"{f_item_tags=}")

        # 3. Toggle fiid's Treeview tags
        if selected:  # Selected == Ture
            # print("Selected == True")
            tree.set(fiid, column="selected", value="True")
            f_item_tags[3] = 'Selected'
            tree.tag_configure(fiid, foreground='red', image=self.icon_delete)
        else:  # Selected == False
            # print("Selected == False")
            tree.set(fiid, column="selected", value="False")
            f_item_tags[3] = 'Not Selected'
            if f_item_tags[2] in 'Original':
                tree.tag_configure(fiid, foreground=D2_C1, image='')
            elif f_item_tags[2] in 'Copy':
                tree.tag_configure(fiid, foreground=D2_C2, image='')
        tree.item(fiid, tags=f_item_tags)  # Update tags


class App(ttk.Frame):
    def __init__(self, master, **options):
        self.master = master
        # 1. Define attributes self.etype and self.layout
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
        super().__init__(master, **options)

        self.find = None
        self.table = None
        self._create_widgets()
        self._create_bindings()

    def _create_widgets(self):
        self.find = Find(self, cfe=self.cfe, layout=self.layout)
        self.find.hide_selected_path()

        self.table = Table(self)
        self.table.set_sdir(self.find.selected_dir)
        self.table.set_sql3db(self.find.sqlite3_db)

        self.find.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        if self.layout in "vertical":
            self.table.grid(row=0, column=1, sticky="nsew", padx=(0, 10),
                            pady=(10, 5))
            self.columnconfigure(1, weight=1)
            self.rowconfigure(0, weight=1)
            self.winfo_toplevel().minsize(width=800, height=450)
        elif self.layout in "horizontal":
            self.table.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
            self.columnconfigure(0, weight=1)
            self.rowconfigure(1, weight=1)
            self.winfo_toplevel().minsize(width=1200, height=500)

    def _create_bindings(self):
        self.find.unbind("<<DirectorySelected>>")
        self.find.bind("<<DirectorySelected>>", self.event_reset_app)
        self.find.bind("<<Sqlite3DBPopulated>>",
                       self.table.event_populate_tree_the_first_time)
        self.table.bn_delete.bind("<<DeletionDone>>", self.event_recheck)

    def event_reset_app(self, event):
        # print(f"\ndef reset_app(self, event):")
        # 2. Reset Table
        if self.table.tree.get_children():
            # print(f"Reset table")
            self.table.reset_table()
        self.table.set_tree_column0_heading_text(self.table.sdir.get())
        # 1. Enable find button
        self.find.bn_find.instate(["disabled"], self.find.enable_find_button)

    def event_recheck(self, event):
        # print(f"\ndef event_recheck(self, event):")
        print(f"\nRecheck {self.find.selected_dir.get()}")
        self.find.reset()
        self.event_reset_app(event)
        self.find.bn_find.invoke()

    def exit(self):
        self.find.exit()


if __name__ == '__main__':
    import w_ttkstyle
    from w_find import Find
    from PIL import ImageTk

    root = tk.Tk()
    root["background"] = BG
    root.title('ANY DUPLICATED PHOTOS?')

    # Commands to create icon
    app_icon = str(CWD) + "/icons/app/ADP.png"
    wm_icon = ImageTk.PhotoImage(file=app_icon)
    wm_icon.image = app_icon
    root.tk.call('wm', 'iconphoto', root, wm_icon)

    s = ttk.Style()
    style = w_ttkstyle.customise_ttk_widgets_style(s)

    app = App(root, cfe="process", layout="vertical")
    # app = App(root, cfe="process", layout="horizontal")
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
