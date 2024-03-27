# print(f"{__name__}")

# Package modules
exclude = ["exclude", "functions", "widgets"]

__all__ = [
	name for name in dir()
	if not name.startswith('_') and not name.startswith("w_")
	and name not in exclude
]
# print(f"adp {__all__=}")

__version__ = '0.1'
__author__ = 'Chia Yan Hon, Julian.'
__copyright__ = "Copyright 2023, Chia Yan Hon, Julian."
__license__ = "Apache License, Version 2.0"
