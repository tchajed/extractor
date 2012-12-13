""" Helpful utility functions and classes for working with swig.  """

from libxtract import xtract

def args(*args):
	""" Prepare arguments for use as argv in libxtract.

	Allocates its own space for thread safety.

	"""
	array = xtract.floatArray(len(args))
	for i, arg in enumerate(args):
		array[i] = float(arg)
	return xtract.floata_to_voidp(array)

class CArray:
  """
  Wraps a Swig C array with a length into a pythonic object.

  Supports len(), indexing with [], and iteration.
  """
  def __init__(self, a, n):
    self.a = a
    self.n = n
  def __len__(self):
    return self.n
  def __getitem__(self, index):
    return self.a[index]
  def __iter__(self):
    i = 0
    while i < self.n:
      yield self.a[i]
      y += 1

