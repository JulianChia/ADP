# print(f"{__name__}")

# Python modules
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import font

# Project modules
from adp.functions import filesize
from adp.widgets.constants import D1_C0, D1_C1, D1_C2, BG, FG, TFONT, DFONT, BFONT

__all__ = ["Findings", "DonutCharts"]
__version__ = '0.1'
__author__ = 'Chia Yan Hon, Julian.'
__copyright__ = "Copyright 2024, Chia Yan Hon, Julian."
__license__ = "Apache License, Version 2.0"


class Findings(ttk.Frame):
    """A Custom widget to display a table of results from invoking the
    bn_find ttk.Button widget that is found in the w_find.py module.

    User Methods:
    .reset()
    .update_subfolders(quantity=0, duration=0.0, dunit='secs')
    .update_photos(quantity=0, duration=0.0, dunit='secs')
    .update_duplicates(quantity=0, duration=0.0, dunit='secs')
    .update_total(duration=0.0, dunit='secs'):
    """

    def __init__(self, master):
        super().__init__(master, width=350, height=115)
        self.nsf = tk.IntVar()  # no. of sub-folders
        self.np = tk.IntVar()   # no. of photos
        self.nd = tk.IntVar()   # no. of duplicates
        self.tsf = tk.StringVar()  # time to find no. of sub-folders
        self.tp = tk.StringVar()   # time to find no. of photos
        self.td = tk.StringVar()   # time to find no. of duplicates
        self.tt = tk.StringVar()   # total time to complete finds
        self.tsf_units = tk.StringVar()  # time units for self.tsf
        self.tp_units = tk.StringVar()   # time units for self.tp
        self.td_units = tk.StringVar()   # time units for self.td
        self.tt_units = tk.StringVar()   # time units for self.tt
        self.title_lb = None
        self.sf_lb1 = None
        self.sf_lb2 = None
        self.sf_lb3 = None
        self.sf_lb4 = None
        self.p_lb1 = None
        self.p_lb2 = None
        self.p_lb3 = None
        self.p_lb4 = None
        self.d_lb1 = None
        self.d_lb2 = None
        self.d_lb3 = None
        self.d_lb4 = None
        self.t_lb1 = None
        self.t_lb3 = None
        self.t_lb4 = None

        self.reset()
        self._create_widgets()

    def _create_widgets(self):
        astyle = dict(style='Title.TLabel')
        bstyle = dict(style='Default.TLabel')

        self.title_lb = ttk.Label(self, text="FINDINGS: ", **astyle)

        self.sf_lb1 = ttk.Label(self, text="Sub-Folders: ", **bstyle)
        self.sf_lb2 = ttk.Label(self, textvariable=self.nsf, **bstyle)
        self.sf_lb3 = ttk.Label(self, textvariable=self.tsf, **bstyle)
        self.sf_lb4 = ttk.Label(self, textvariable=self.tsf_units, **bstyle)

        self.p_lb1 = ttk.Label(self, text="Photos: ", foreground=D1_C0,
                               **bstyle)
        self.p_lb2 = ttk.Label(self, textvariable=self.np, foreground=D1_C0,
                               **bstyle)
        self.p_lb3 = ttk.Label(self, textvariable=self.tp, foreground=D1_C0,
                               **bstyle)
        self.p_lb4 = ttk.Label(self, textvariable=self.tp_units,
                               foreground=D1_C0, **bstyle)

        self.d_lb1 = ttk.Label(self, text="Duplicates: ", foreground=D1_C2,
                               **bstyle)
        self.d_lb2 = ttk.Label(self, textvariable=self.nd, foreground=D1_C2,
                               **bstyle)
        self.d_lb3 = ttk.Label(self, textvariable=self.td, foreground=D1_C2,
                               **bstyle)
        self.d_lb4 = ttk.Label(self, textvariable=self.td_units,
                               foreground=D1_C2, **bstyle)

        self.t_lb1 = ttk.Label(self, text="Total: ", **bstyle)
        self.t_lb3 = ttk.Label(self, textvariable=self.tt, **bstyle)
        self.t_lb4 = ttk.Label(self, textvariable=self.tt_units, **bstyle)

        self.title_lb.grid(row=0, column=0, sticky='nsew', columnspan=3,)
        bb = 15
        aa = 10
        cc = 5
        pad1xy = {'padx': (0, bb), 'pady': (aa, 0)}
        pad2xy = {'padx': (0, bb), 'pady': (cc, 0)}
        self.sf_lb1.grid(row=1, column=0, sticky='nw', **pad1xy)
        self.sf_lb2.grid(row=1, column=1, sticky='ne', **pad1xy)
        self.sf_lb3.grid(row=1, column=2, sticky='ne', pady=(aa, 0))
        self.sf_lb4.grid(row=1, column=3, sticky='nw', pady=(aa, 0),
                         padx=(2, 0))

        self.p_lb1.grid(row=2, column=0, sticky='nw', **pad2xy)
        self.p_lb2.grid(row=2, column=1, sticky='ne', **pad2xy)
        self.p_lb3.grid(row=2, column=2, sticky='ne', pady=(cc, 0))
        self.p_lb4.grid(row=2, column=3, sticky='nw', pady=(cc, 0), padx=(2, 0))

        self.d_lb1.grid(row=3, column=0, sticky='nw', **pad2xy)
        self.d_lb2.grid(row=3, column=1, sticky='ne', **pad2xy)
        self.d_lb3.grid(row=3, column=2, sticky='ne', pady=(cc, 0))
        self.d_lb4.grid(row=3, column=3, sticky='nw', pady=(cc, 0), padx=(2, 0))

        self.t_lb1.grid(row=4, column=0, sticky='nw', **pad2xy)
        self.t_lb3.grid(row=4, column=2, sticky='ne', pady=(cc, 0))
        self.t_lb4.grid(row=4, column=3, sticky='nw', pady=(cc, 0), padx=(2, 0))

    def reset(self):
        self.update_subfolders()
        self.update_photos()
        self.update_duplicates()
        self.update_total()

    def update_subfolders(self, quantity=0, duration=0.0, dunit='secs'):
        if quantity < 0:
            raise AttributeError(f"Attribute quantity must be > 0.")
        if duration < 0:
            raise AttributeError(f"Attribute duration must be > 0.")
        self.nsf.set(quantity)
        self.tsf.set(f'{duration:.3f}')
        self.tsf_units.set(dunit)

    def update_photos(self, quantity=0, duration=0.0, dunit='secs'):
        if quantity < 0:
            raise AttributeError(f"Attribute quantity must be > 0.")
        if duration < 0:
            raise AttributeError(f"Attribute duration must be > 0.")
        self.np.set(quantity)
        self.tp.set(f'{duration:.3f}')
        self.tp_units.set(dunit)

    def update_duplicates(self, quantity=0, duration=0.0, dunit='secs'):
        if quantity < 0:
            raise AttributeError(f"Attribute quantity must be > 0.")
        if duration < 0:
            raise AttributeError(f"Attribute duration must be > 0.")
        self.nd.set(quantity)
        self.td.set(f'{duration:.3f}')
        self.td_units.set(dunit)

    def update_total(self, duration=0.0, dunit='secs'):
        if duration < 0:
            raise AttributeError(f"Attribute duration must be > 0.")
        self.tt.set(f'{duration:.3f}')
        self.tt_units.set(dunit)


class DonutCharts(tk.Canvas):
    """A Custom widget to display a Ring Chart of results from invoking
    the bn_find ttk.Button widget that is found in the w_find.py module.

    User Methods:
    .reset()
    .update_gui(qo, qc, so, sc)
    .resize()
    """
    def __init__(self, master, quantity1=0, quantity2=0, size1=0, size2=0,
                 title0="Title0", title1="Title1", title2="Title2",
                 legend1="Legend1", legend2="Legend2", bg=BG, fg=FG,
                 color0=FG, color1=FG, color2=FG):
        if quantity1 < 0:
            raise AttributeError(f"Attribute quantity1 must be > 0.")
        if quantity2 < 0:
            raise AttributeError(f"Attribute quantity2 must be > 0.")
        if size1 < 0:
            raise AttributeError(f"Attribute size1 must be > 0.")
        if size2 < 0:
            raise AttributeError(f"Attribute size2 must be > 0.")
        super().__init__(master, bg=BG, bd=0, highlightthickness=0, width=365,
                         height=133)
        self.master = master
        self.quantity1 = quantity1
        self.quantity2 = quantity2
        self.quantity_t = quantity1 + quantity2
        self.size1 = (size1, "B")
        self.size2 = (size2, "B")
        self.size_t = (size1 + size2, "B")
        # print(self.quantity1, self.quantity2, self.size1, self.size2, )
        self.title0 = title0
        self.title1 = title1
        self.title2 = title2
        self.legend1 = legend1
        self.legend2 = legend2
        self.bg = bg
        self.fg = fg
        self.color0 = color0
        self.color1 = color1
        self.color2 = color2
        self.q1_arc = None
        self.q2_arc = None
        self.q1b_arc = None
        self.q2b_arc = None
        self.q1_text = None
        self.q2_text = None
        self.s1_arc = None
        self.s2_arc = None
        self.s1b_arc = None
        self.s2b_arc = None
        self.s1_text = None
        self.s2_text = None
        self.qt_text = None
        self.st_text = None
        self.l_sq1 = None
        self.l_sq2 = None
        self.l_text1 = None
        self.l_text2 = None
        self.tt1_text = None
        self.tt2_text = None

        self._create_gui()
        # self.reset()

    def _create_gui(self):
        # Angles for quantity
        q1 = q2 = 0.5 * 360

        # Angles for size
        s1 = s2 = 0.5 * 360

        # Pixel coordinates in tk.Canvas
        title_dy = 20  # titles' height
        title_pady = 5
        title_y = title_dy + title_pady
        # Gap
        gap_x = 110  # btw top-right & top-left corners of 1st and 2nd donuts
        # 1st Donut
        diameter = 90
        x0 = 0               # x of top-left corner of 1st donut
        y0 = x0 + title_y    # y ditto
        x1 = diameter        # x of bottom-right corner of 1st donut
        y1 = x1 + title_y    # y ditto
        # Donut Blank core
        bx0 = 20             # x of top-left corner of 1st donut blank
        by0 = bx0 + title_y  # y ditto
        bx1 = 70             # x of bottom-right corner of 1st donut blank
        by1 = bx1 + title_y  # y ditto
        # Interval
        xinterval = x0 + x1 + gap_x    # x of top-left corner of 2nd donut
        # Donut's Text
        d1t1x = x1 + 5   # x of text for 1st & 2nd donuts values
        d1t2x = d1t1x
        d1t1y = title_y + diameter * 0.35   # y of text for 1st donut value
        d1t2y = title_y + diameter * 0.65   # y of text for 2nd donut value
        d2t1x = d1t1x + xinterval
        d2t2x = d2t1x
        d2t1y = d1t1y
        d2t2y = d1t2y
        # Title
        tt0x = int((x0 + x1) / 2)  # x of 1st Donut title bottom-left corner
        tt0y = 10                  # y ditto
        tt1x = tt0x  # x of 1st Donut title bottom-left corner
        tt1y = x1 * 0.5 + title_y  # y ditto
        tt2x = tt1x + xinterval    # x of 2nd Donut title bottom-left corner
        tt2y = tt1y  # y ditto
        # Total
        ttx = d1t1x         # x of total value of 1st donut
        tty = d1t1y - 25    # y of total value of 1st & 2nd donuts
        # Legend
        lr1x0 = x1 + gap_x * 0.4   # x of legend square top-left corner
        lr1y0 = y1 - 15            # y ditto
        lr1x1 = lr1x0 + 10   # x of legend square bottom-right corner
        lr1y1 = lr1y0 + 10   # y ditto
        lt1x = lr1x1 + 10    # x of legend text
        lt1y = lr1y0 + 5     # y ditto
        lr2x0 = lr1x0
        lr2y0 = lr1y1 + 5
        lr2x1 = lr2x0 + 10   # x of legend square bottom-right corner
        lr2y1 = lr2y0 + 10   # y ditto
        lt2x = lr2x1 + 10    # x of legend text
        lt2y = lr2y0 + 5     # y ditto
        tfont = font.Font(**TFONT)  # title font
        dfont = font.Font(**DFONT)  # results font
        bfont = font.Font(**BFONT)  # bold font
        look1 = {"fill": self.color1, "outline": BG}
        look2 = {"fill": self.color2, "outline": BG}
        lookblank = {"fill": BG, "outline": BG}

        # 1st Donut : Quantity has segments 1 & 2
        self.q1_arc = self.create_arc(
            x0, y0, x1, y1, start=0, extent=q1, tags=['DONUT1', 'ARC'],
            **look1)
        self.q2_arc = self.create_arc(
            x0, y0, x1, y1, start=q1, extent=q2, tags=['DONUT1', 'ARC'],
            **look2)
        self.q1b_arc = self.create_arc(
            bx0, by0, bx1, by1, start=0, extent=q1, tags=['DONUT1', 'ARC'],
            **lookblank)
        self.q2b_arc = self.create_arc(
            bx0, by0, bx1, by1, start=q1, extent=q2, tags=['DONUT1', 'ARC'],
            **lookblank)
        self.q1_text = self.create_text(
            d1t1x, d1t1y, fill=self.color1, anchor='w', font=dfont,
            text=f'q1_text', tags=['DONUT1', "TEXT"])
        self.q2_text = self.create_text(
            d1t2x, d1t2y, fill=self.color2, anchor='w', font=dfont,
            text='q2_text', tags=['DONUT1', "TEXT"])

        # 2nd Donut : Size (Bytes) has segments 1 & 2
        self.s1_arc = self.create_arc(
            x0+xinterval, y0, x1+xinterval, y1, start=0, extent=s1,
            tags=['DONUT2', 'ARC'], **look1)
        self.s2_arc = self.create_arc(
            x0+xinterval, y0, x1+xinterval, y1, start=s1, extent=s2,
            tags=['DONUT2', 'ARC'], **look2)
        self.s1b_arc = self.create_arc(
            bx0+xinterval, by0, bx1+xinterval, by1, start=0, extent=359,
            tags=['DONUT2', 'ARC'], **lookblank)
        self.s2b_arc = self.create_arc(
            bx0+xinterval, by0, bx1+xinterval, by1, start=180, extent=s2,
            tags=['DONUT2', 'ARC'], **lookblank)
        self.s1_text = self.create_text(
            d2t1x, d2t1y, fill=self.color1, anchor='w', font=dfont,
            text='s1_text', tags=['DONUT2', 'TEXT'],)
        self.s2_text = self.create_text(
            d2t2x, d2t2y, fill=self.color2, anchor='w', font=dfont,
            text='s2_text', tags=['DONUT2', 'TEXT'],)

        # Totals
        self.qt_text = self.create_text(
            ttx, tty, fill=self.color0, anchor='w', font=dfont,  text='qt_text',
            tags=['DONUT1', 'TEXT'])
        self.st_text = self.create_text(
            ttx + xinterval, tty, fill=self.color0, anchor='w', font=dfont,
            text='st_text', tags=['DONUT2', 'TEXT'])

        # Legend
        self.l_sq1 = self.create_rectangle(
            lr1x0, lr1y0, lr1x1, lr1y1, fill=self.color1, outline=self.bg,
            tags=['DONUT1', 'LEGEND'])
        self.l_sq2 = self.create_rectangle(
            lr2x0, lr2y0, lr2x1, lr2y1, fill=self.color2, outline=self.bg,
            tags=['DONUT2', 'LEGEND'])
        self.l_text1 = self.create_text(
            lt1x, lt1y, text=f'{self.legend1}', fill=self.color1,
            anchor='w', font=dfont, tags=['DONUT1', 'LEGEND'])
        self.l_text2 = self.create_text(
            lt2x, lt2y, text=f'{self.legend2}', fill=self.color2,
            anchor='w', font=dfont, tags=['DONUT2', 'LEGEND'])

        # Titles
        self.tt0_text = self.create_text(
            tt0x, tt0y, text=f"{self.title0}", fill=self.color0,
            anchor="center", font=bfont, tags=['DONUT1', 'TITLE'])
        self.tt1_text = self.create_text(
            tt1x, tt1y, text=f"{self.title1}", fill=self.fg, anchor="center",
            font=dfont, tags=['DONUT1', 'TITLE'])
        self.tt2_text = self.create_text(
            tt2x, tt2y, text=f"{self.title2}", fill=self.fg, anchor="center",
            font=dfont, tags=['DONUT2', 'TITLE'])

    def reset(self):
        look1 = {"fill": self.bg, "outline": self.color1}
        look2 = {"fill": self.bg, "outline": self.color2}

        # Amend Original appearances when no duplicated photos
        for i in [self.q1_arc, self.q1b_arc, self.s1_arc, self.s1b_arc]:
            self.itemconfigure(i, style=tk.ARC, **look1)
        for i in [self.q1_text, self.q2_text, self.qt_text]:
            self.itemconfigure(i, text=f'0  ({0:.2f}%)')

        # Amend Copies appearances when no photos
        for i in [self.q2_arc, self.q2b_arc, self.s2_arc, self.s2b_arc]:
            self.itemconfigure(i, style=tk.ARC, **look2)
        for i in [self.s1_text, self.s2_text, self.st_text]:
            self.itemconfigure(i, text=f'0.0 B  ({0:.2f}%)')

        # Update Canvas size
        self.resize()

    def update_gui(self, qo, qc, so, sc):
        vmin = 0.005 * 360  # lower bound value
        vmax = 0.995 * 360  # upper bound value

        def filter_extremes(v):
            """Function to filter out extreme scenarios of 0 and 360 and
            replace these values with psuedo values to facilitate the
            displaying of tk.Canvas.create_arc objects."""
            if v <= vmin:
                return vmin
            elif v >= vmax:
                return vmax
            else:
                return v

        qtotal = qo + qc
        if qtotal != 0:
            q1 = filter_extremes(qo / qtotal * 360)
            q2 = filter_extremes(qc / qtotal * 360)
            q1_percent = qo / qtotal * 100
            q2_percent = qc / qtotal * 100
            self.quantity1 = qo
            self.quantity2 = qc
            self.quantity_t = qtotal

            stotal = so + sc
            s1 = filter_extremes(so / stotal * 360)
            s2 = filter_extremes(sc / stotal * 360)
            s1_percent = so / stotal * 100
            s2_percent = sc / stotal * 100
            self.size1 = filesize(so)
            self.size2 = filesize(sc)
            self.size_t = filesize(stotal)

            look1 = {"style": tk.PIESLICE, "fill": self.color1,
                     "outline": self.bg}
            look2 = {"style": tk.PIESLICE, "fill": self.color2,
                     "outline": self.bg}
            lookblank = {"style": tk.PIESLICE, "fill": self.bg,
                         "outline": self.bg}

            # Amend appearances of 1st Donut
            # Update Arcs
            self.itemconfigure(self.q1_arc, start=0, extent=q1, **look1)
            self.itemconfigure(self.q2_arc, start=q1, extent=q2, **look2)
            self.itemconfigure(self.q1_text,
                               text=f'{self.quantity1}  ({q1_percent:.2f}%)')
            self.itemconfigure(self.q2_text,
                               text=f'{self.quantity2}  ({q2_percent:.2f}%)')
            self.itemconfigure(self.qt_text,
                               text=f'{self.quantity_t}  ({100:.2f}%)')

            # Amend appearances of 2nd Donut
            self.itemconfigure(self.s1_arc, start=0, extent=s1, **look1)
            self.itemconfigure(self.s2_arc, start=s1, extent=s2, **look2)
            self.itemconfigure(self.s1_text,
                               text=f'{self.size1[0]:.2f} {self.size1[1]}'
                                    f'  ({s1_percent:.2f}%)')
            self.itemconfigure(self.s2_text,
                               text=f'{self.size2[0]:.2f} {self.size2[1]}'
                                    f'  ({s2_percent:.2f}%)')
            self.itemconfigure(self.st_text,
                               text=f'{self.size_t[0]:.2f} {self.size_t[1]}'
                                    f'  ({100:.2f}%)')

            # Amend appearances of Blanks in 1st and 2nd Donuts
            for i in [self.q1b_arc, self.q2b_arc, self.s1b_arc, self.s2b_arc]:
                self.itemconfigure(i, **lookblank)

            # Update Canvas size
            self.resize()

    def resize(self):
        self.update_idletasks()
        boundary = self.bbox(tk.ALL)
        # print(f'{boundary=}')
        width = boundary[2]-boundary[0]
        height = boundary[3] - boundary[1]
        self['width'] = width
        self['height'] = height
        self.update_idletasks()


if __name__ == "__main__":
    from adp import functions as func, widgets as ttkstyle

    root = tk.Tk()
    # root['bg'] = BG
    root['bg'] = 'orange'
    s = ttk.Style()
    style = ttkstyle.customise_ttk_widgets_style(s)
    dw = DonutCharts(root, color0=FG, color1=D1_C1, color2=D1_C2)
    dw.grid(row=0, column=1, sticky='nw')
    quantity_o = 963
    quantity_c = 1158
    size_o = 1811754583
    size_c = 2144219048
    # quantity_o = 963
    # quantity_c = 0
    # size_o = 1811754583
    # size_c = 0
    # dw.update_gui(quantity_o, quantity_c, size_o, size_c)
    dw.reset()

    tw = Findings(root)
    tw.grid(row=0, column=0, sticky='nw', padx=(0, 20))
    # Define Quantities
    nsf = 32         # nsubfolders
    np = 2140        # nphotos
    no = quantity_o  # noriginals
    nc = quantity_c  # ncopies
    nd = no + nc     # nduplicates
    # Update Quantities
    tw.nsf.set(nsf)
    tw.np.set(np)
    tw.nd.set(nd)
    # Define Timings
    tsf = 0.004986518993973732  # sec  tsubfolders
    tp = 66.23401878005825      # sec  tphotos
    td = 0.6218715249560773     # sec  tduplicates
    tt = tsf + tp + td
    # print(f'{tt=}')
    tsf, tsf_units = func.timings(tsf)
    tp, tp_units = func.timings(tp)
    td, td_units = func.timings(td)
    tt, tt_units = func.timings(tt)
    # print(f'{tsf=} {tsf_units=}')
    # print(f'{tp=} {tp_units=}')
    # print(f'{td=} {td_units=}')
    # print(f'{tt=} {tt_units=}')
    # Update Timings
    tw.tsf.set(f"{tsf:.3f}")
    tw.tp.set(f"{tp:.3f}")
    tw.td.set(f"{td:.3f}")
    tw.tt.set(f"{tt:.3f}")
    tw.tsf_units.set(tsf_units)
    tw.tp_units.set(tp_units)
    tw.td_units.set(td_units)
    tw.tt_units.set(tt_units)
    tw.reset()
    # print(f'{tw.sf_lb1["style"]=}')
    # print(f'{s.lookup(tw.sf_lb1["style"], "font")=}')

    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)
    root.mainloop()
