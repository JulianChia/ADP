# Python modules
import tkinter as tk
import tkinter.ttk as ttk

__all__ = ["Progressbarwithblank"]
__version__ = '0.1.1'
__license__ = "Apache License, Version 2.0"
__copyright__ = "Copyright 2024, Chia Yan Hon, Julian."
__author__ = 'Chia Yan Hon, Julian.'
__email__ = "julianchiayh@gmail.com"


class Progressbarwithblank(ttk.Progressbar):
	"""A custom ttk.Progressbar widget with a blank. """

	def __init__(self, master, second=False, **options):
		super().__init__(master, **options)
		self.master = master
		self.options = options
		self.blank = ttk.Label(master, text="")
		self.second = second
		self.pb2 = ttk.Progressbar(master, **options)

	def show(self):
		self.lift(aboveThis=self.blank)

	def hide(self):
		self.lower(belowThis=self.blank)

	def show_pb2(self):
		if self.second:
			self.pb2.lift(aboveThis=self.blank)

	def hide_pb2(self):
		if self.second:
			self.pb2.lower(belowThis=self.blank)

	def grid_pb(
			self, in_=None, row=0, rowspan=1, column=0, columnspan=1, padx=0,
			pady=0, ipadx=0, ipady=0, sticky="",):
		"""Method to automatically grid both the ttk.Progressbar and the
		ttk.Label at the same location."""
		blank_sticky = "nsew"
		if in_:
			self.blank.grid(
				in_=in_, row=row, rowspan=rowspan, column=column,
				columnspan=columnspan, padx=padx, pady=pady, ipadx=ipadx,
				ipady=ipady, sticky=blank_sticky)
			self.grid(
				in_=in_, row=row, rowspan=rowspan, column=column,
				columnspan=columnspan, padx=padx, pady=pady, ipadx=ipadx,
				ipady=ipady, sticky=sticky)
			if self.second:
				self.pb2.grid(
					in_=in_, row=row, rowspan=rowspan, column=column,
					columnspan=columnspan, padx=padx, pady=pady, ipadx=ipadx,
					ipady=ipady, sticky=sticky)
		else:
			self.blank.grid(
				in_=self.master, row=row, rowspan=rowspan, column=column,
				columnspan=columnspan, padx=padx, pady=pady, ipadx=ipadx,
				ipady=ipady, sticky=blank_sticky)
			self.grid(
				in_=self.master, row=row, rowspan=rowspan, column=column,
				columnspan=columnspan, padx=padx, pady=pady, ipadx=ipadx,
				ipady=ipady, sticky=sticky)
			if self.second:
				self.pb2.grid(
					in_=self.master, row=row, rowspan=rowspan, column=column,
					columnspan=columnspan, padx=padx, pady=pady, ipadx=ipadx,
					ipady=ipady, sticky=sticky)
		self.show()


if __name__ == "__main__":
	root = tk.Tk()
	progress = tk.IntVar()
	progress.set(0)
	pb1 = Progressbarwithblank(root, orient="horizontal", mode='indeterminate')
	pb2 = Progressbarwithblank(
		root, orient="vertical", mode='indeterminate', second=True)
	pb2.pb2.configure(mode="determinate", variable=progress)
	pb1.grid_pb(row=0, column=0, sticky='nsew')
	pb2.grid_pb(row=1, column=1, sticky='nsew')
	# pb1.hide()
	# pb2.show()
	pb1.start(20)
	pb2.start(10)

	def show_pb2():
		i = progress.get()
		progress.set(i+1)
		if i < 100:
			pb2.after(100, show_pb2)
		else:
			pb2.hide_pb2()
			pb2.show()

	root.after(3000, show_pb2)
	pb2.hide()
	pb2.show_pb2()

	root.columnconfigure(0, weight=1)
	root.rowconfigure(1, weight=1)
	root.mainloop()
