""" Helpful utility functions and classes for working with swig.  """

from libxtract import xtract

f = xtract.floatArray(1)

def floatPtr(val):
	f[0] = float(val)
	return f

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

