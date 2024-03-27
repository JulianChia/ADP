# print(f"{__name__}")

# Python modules
import tkinter as tk
import tkinter.ttk as ttk

__all__ = ["Progressbarwithblank"]
__version__ = '0.1'
__author__ = 'Chia Yan Hon, Julian.'
__copyright__ = "Copyright 2024, Chia Yan Hon, Julian."
__license__ = "Apache License, Version 2.0"


class Progressbarwithblank(ttk.Progressbar):
	"""A custom ttk.Progressbar widget with a blank. """

	def __init__(self, master, **options):
		super().__init__(master, **options)
		self.master = master
		self.options = options
		self.blank = ttk.Label(master, text="")

	def show(self):
		self.lift(aboveThis=self.blank)

	def hide(self):
		self.lower(belowThis=self.blank)

	def grid_pb(self, in_=None, row=0, rowspan=1, column=0, columnspan=1,
				padx=0, pady=0, ipadx=0, ipady=0, sticky="",
				):
		"""Method to automatically grid both the ttk.Progressbar and the
		ttk.Label at the same location."""
		blank_sticky = "nsew"
		if in_:
			self.blank.grid(in_=in_, row=row, rowspan=rowspan, column=column,
							columnspan=columnspan, padx=padx, pady=pady,
							ipadx=ipadx, ipady=ipady, sticky=blank_sticky)
			self.grid(in_=in_, row=row, rowspan=rowspan, column=column,
					  columnspan=columnspan, padx=padx, pady=pady,
					  ipadx=ipadx, ipady=ipady, sticky=sticky)
		else:
			self.blank.grid(in_=self.master, row=row, rowspan=rowspan,
							column=column, columnspan=columnspan, padx=padx,
							pady=pady, ipadx=ipadx, ipady=ipady,
							sticky=blank_sticky)
			self.grid(in_=self.master, row=row, rowspan=rowspan, column=column,
					  columnspan=columnspan, padx=padx, pady=pady, ipadx=ipadx,
					  ipady=ipady, sticky=sticky)
		self.show()


if __name__ == "__main__":
	root = tk.Tk()
	pb1 = Progressbarwithblank(root, orient="horizontal", mode='indeterminate')
	pb2 = Progressbarwithblank(root, orient="vertical", mode='indeterminate')
	pb1.grid_pb(row=0, column=0, sticky='nsew')
	pb2.grid_pb(row=1, column=1, sticky='nsew')
	pb1.hide()
	# pb2.show()
	pb1.start(20)
	pb2.start(10)
	root.columnconfigure(0, weight=1)
	root.rowconfigure(1, weight=1)
	root.mainloop()
