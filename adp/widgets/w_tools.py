# print(f"{__name__}")

# Python modules
import tkinter as tk
import tkinter.font

__all__ = ["string_pixel_size", "get_geometry_values", "str_geometry_values"]
__version__ = '0.1'
__author__ = 'Chia Yan Hon, Julian.'
__copyright__ = "Copyright 2024, Chia Yan Hon, Julian."
__license__ = "Apache License, Version 2.0"


def string_pixel_size(text, family, size, weight=tk.NORMAL, slant="roman",
                      underline=False, overstrike=False):
    """ Function returns the width and height of a given text.
    Args:
     family	The font family name as a string.
     size	The font height as an integer in points. To get a font n pixels
            high, use -n.

    Kwargs:
     weight	'bold' for boldface, 'normal' for regular weight.
     slant	'italic' for italic, 'roman' for unslanted.
     underline	1 for underlined text, 0 for normal.
     overstrike	1 for overstruck text, 0 for normal.
    """
    rfont = tk.font.Font(family=family, size=size, weight=weight, slant=slant,
                         underline=underline, overstrike=overstrike)
    w = rfont.measure(text)  # string pixel width
    h = rfont.metrics("linespace")  # string pixel height
    return w, h


def get_geometry_values(geo: str):
    """Function to return the integer values of the (width, height, x, y) that
    is returned by tkinter w.winfo_geometry() method."""
    width = int(geo[:geo.index("x")])
    height = int(geo[geo.index("x")+1:geo.index("+")])
    xy = geo[geo.index("+")+1:]
    x = int(xy[:xy.index("+")])
    y = int(xy[xy.index("+")+1:])
    # print(f"{width=} {height=} {x=} {y=}")
    return width, height, x, y


def str_geometry_values(width: int, height: int, x: int, y: int):
    """Function to return the str "widthxheight+x+y" that is arg of
    the w.geometry() method of widgets tk.Tk() and tk.Toplevel()."""
    return f"{width}x{height}+{x}+{y}"


if __name__ == "__main__":
    geom = '602x355+50+114'
    aa = get_geometry_values(geom)
    print(f"{aa=}")

    bb = str_geometry_values(104, 30, 500, 400)
    print(f"{bb=}")
