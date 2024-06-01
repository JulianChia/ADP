# Python modules
import tkinter as tk
import tkinter.ttk as ttk

# Project modules
from adp.widgets.constants import *

__all__ = ["customise_ttk_widgets_style", "stylename_elements_options"]
__version__ = '0.1.1'
__license__ = "Apache License, Version 2.0"
__copyright__ = "Copyright 2024, Chia Yan Hon, Julian."
__author__ = 'Chia Yan Hon, Julian.'
__email__ = "julianchiayh@gmail.com"

def customise_ttk_widgets_style(ss):
    dfont = list(DFONT.values())
    bfont = list(BFONT.values())
    tfont = list(TFONT.values())

    # ss.theme_use('alt')
    # ss.theme_use('clam')
    # ss.theme_use('classic')
    ss.theme_use('default')

    # All Widgets
    ss.configure(".", font=dfont, background=BG, foreground=FG, cap=tk.ROUND,
                 join=tk.ROUND)

    # ttk.Frame
    # ss.configure('TFrame', background=BG, borderwidth=0)  # For debugging
    # ss.configure('Main.TFrame', background='pink')  # For debugging
    # ss.configure('About.TFrame', background="gray",)  # For debugging
    # ss.configure('Gframe.TFrame', background='green')  # For debugging
    # ss.configure('Framebns.TFrame', background="violet")  # For debugging
    # ss.configure('TableFrame.TFrame', background="red", borderwidth=0)  # For debugging

    # Default ttk.Button
    ss.configure('TButton', padding=5, relief=tk.FLAT, background=BG,
                 foreground=FG)
    ss.configure('Delete.TButton', padding=5, relief=tk.FLAT, background="red",
                 foreground=FG)
    ss.map('TButton',
           foreground=[("disabled", 'grey'),
                       ('pressed', 'yellow'),
                       ('active', 'yellow'), ],
           background=[('disabled', '#646a67'),
                       ('pressed', '!focus', BG),
                       ('active', C0_light)],
           relief=[('pressed', 'sunken'), ('!pressed', 'raised')],
           )

    # ttk.Label
    ss.configure('TLabel', padding=0, font=dfont, background=BG, foreground=FG)
    ss.map('TLabel',
           foreground=[('disabled', 'grey')],
           background=[('disabled', '#646a67')],
           )
    ss.configure('Title.TLabel', padding=0, font=tfont)
    ss.configure('Bold.TLabel', padding=0, font=bfont)
    ss.configure('Default.TLabel', padding=0, font=dfont)
    ss.configure("Blank.TLabel", padding=0, font=dfont, background=BG)

    # ttk.Progressbar
    ss.configure("Vertical.TProgressbar", thickness=PB_THICKNESS,
                 background=PB_COLOR)
    ss.configure("Horizontal.TProgressbar", thickness=PB_THICKNESS,
                 background=PB_COLOR)

    # Widgets of DupGroup
    # Real
    ss.configure('DupGroup.TFrame', background=BG2)
    ss.configure('infoframe.TFrame', background=BG2)
    ss.configure('infoframe.TLabel', background=BG2, foreground=FG, font=bfont)
    ss.configure("vp.TLabel", background=BG2, foreground=FG2)
    # Debug
    # ss.configure('DupGroup.TFrame', background="purple")
    # ss.configure('infoframe.TFrame', background="yellow")
    # ss.configure('infoframe.TLabel', background="green", font=bfont,
    #              foreground=FG)
    # ss.configure("vp.TLabel", background="orange", foreground="green")
    # ttk.Checkbutton
    ss.layout('TCheckbutton', [('Checkbutton.padding',
                               {'sticky': 'nswe', 'children':
                                   [('Checkbutton.indicator',
                                     {'side': 'bottom', 'sticky': ''}),
                                    ('Checkbutton.focus',
                                     {'side': 'left', 'sticky': 'w',
                                      'children': [('Checkbutton.label',
                                                    {'sticky': 'nswe'})]
                                      })
                                    ]})
                               ])
    ss.map('TCheckbutton',
           foreground=[("disabled", 'grey'),
                       ('pressed', 'yellow'),
                       ('active', 'yellow'), ],
           background=[('disabled', '#646a67'),
                       ('pressed', '!focus', BG),
                       ('active', C0_light)],
           relief=[('pressed', 'sunken'),
                   ('!pressed', 'raised')],
           indicatorcolor=[('pressed', '#ececec'),
                           ('!disabled', 'alternate', '#9fbdd8'),
                           ('disabled', 'alternate', '#c0c0c0'),
                           # ('!disabled', 'selected', '#4a6984'),  # original
                           # ('!disabled', 'selected', '#e35d18'),  # change this color
                           ('!disabled', 'selected', 'red'),  # change this color
                           ('disabled', 'selected', '#a3a3a3')],
           )
    ss.configure("TCheckbutton", background=BG2, foreground=FG)

    # ttk.Treeview
    ss.configure('Treeview', background=BG, fieldbackground=BG, foreground=FG,
                 font=dfont)
    ss.configure("Treeview.Heading", font=bfont, padding=5, foreground=FG,
                 relief="flat")
    ss.map("Treeview.Heading", background=[('active', BG)])
    # ss.map("Treeview",
    #       foreground=[('disabled', '#a3a3a3'),
    #                   ('selected', 'red'),
    #                   ],
    #       background=[('disabled', '#d9d9d9'),
    #                   ('selected', "#8cbdee"),
    #                   ]
    #       )

    # ttk.Panedwindow
    ss.configure("TPanedwindow", background="orange")
    # ss.configure("TPanedwindow", background="#8c8cee")

    # ttk.Scrollbar
    ss.configure("Vertical.TScrollbar", gripcount=3, troughcolor="gray",
                 # background=C0, darkcolor=C0_dark, lightcolor=C0_light,
                 bordercolor=BG, arrowcolor=FG)
    ss.map("TScrollbar", background=[('active', C0_light)])
    ss.configure("Horizontal.TScrollbar", gripcount=3, troughcolor="gray",
                 # background=C0, darkcolor=C0_dark, lightcolor=C0_light,
                 bordercolor=BG, arrowcolor=FG)
    ss.map("HScrollbar", background=[('active', C0_light)])

    # About ttk.Button
    ss.layout('About.TButton',
              [(
                  'Button.border',
                  {'sticky': 'nswe',
                   'border': '1',
                   'children': [(
                       # 'Button.focus',
                       # {'sticky': 'nswe',
                       #  'children': [(
                       'Button.padding',
                       {'sticky': 'nswe',
                        'children': [(
                            'Button.label', {'sticky': 'nswe'})
                        ]
                        }
                       # )]
                       # }
                   )]
                   }
              )]
              )

    ss.map('About.TButton',
           foreground=[("disabled", 'grey'),
                       ('pressed', 'yellow'),
                       ('active', 'yellow'), ],
           background=[('disabled', '#646a67'),
                       ('pressed', '!focus', BG),
                       ('active', C0_light)],
           relief=[('pressed', 'sunken'), ('!pressed', 'flat')],
           )

    return ss


def stylename_elements_options(stylename):
    """Function to expose the options of every element associated to a widget
       stylename.

    source:
    https://github.com/sunbearc22/tkinterWidgets/blob/master/tkinterMethods
    """
    try:
        # Get widget elements
        style = ttk.Style()
        layout = str(style.layout(stylename))
        print('\nStylename = {}'.format(stylename))
        print('Layout    = {}'.format(layout))
        elements = []
        for n, x in enumerate(layout):
            if x == '(':
                element = ""
                for y in layout[n+2:]:
                    if y != ',':
                        element = element+str(y)
                    else:
                        elements.append(element[:-1])
                        break
        print('\nElement(s) = {}\n'.format(elements))

        # Get options of widget elements
        for element in elements:
            print('{0:30} options: {1}'.format(
                element, style.element_options(element)))

    except tk.TclError:
        print('_tkinter.TclError: "{0}" in function'
              'widget_elements_options({0}) is not a regonised stylename.'
              .format(stylename))


if __name__ == "__main__":
    root = tk.Tk()
    root['background'] = BG
    s = ttk.Style()
    s = customise_ttk_widgets_style(s)  # This function is causing problem
    button = ttk.Button(root, text="ttk.Button (!disabled)")
    dbutton = ttk.Button(root, text="ttk.Button (disabled)")
    dbutton.state(['!disabled', 'disabled'])
    label = ttk.Label(root, text="ttk.Label (!disabled)")
    dlabel = ttk.Label(root, text="ttk.Label (disabled)")
    dlabel.state(['!disabled', 'disabled'])
    cb = ttk.Checkbutton(root, text="ttk.Checkbutton (!disabled)")
    button.grid(row=0, column=0)
    dbutton.grid(row=0, column=1)
    label.grid(row=1, column=0)
    dlabel.grid(row=1, column=1)
    cb.grid(row=2, column=0)

    # stylename_elements_options('Vertical.TScrollbar')
    # print(f"{s.lookup('Vertical.TScrollbar', 'background')=}")
    # print(f"{s.lookup('Vertical.TScrollbar', 'thumb')=}")
    # print(f"{s.map('Vertical.TScrollbar')=}")
    # print(f"{s.map('TScrollbar')=}")
    # print(f"{s.map('TButton')=}")
    # stylename_elements_options('TCheckbutton')
    # print(f"{s.map('TCheckbutton', 'indicatorcolor')=}")
    stylename_elements_options('Treeview')
    print(f"{s.map('Treeview')=}")
    stylename_elements_options('Treeview.Heading')
    # print(f"{s.lookup('Treeview.Heading')=}")
    # print(f"{s.lookup('Treeview')=}")
    # stylename_elements_options('Vertical.TProgressbar')
    # stylename_elements_options('TPanedwindow')

    root.mainloop()
