# vim: tw=80:ts=2:sw=2:et:sta
"""
Wrapper for sound files.

"""

from __future__ import print_function
import itertools
import os
import re
import wave
import numpy as np

class SoundFile:
  def __len__(self):
    return len(self.samples())
  def __init__(self, file):
    """ Instantiate a SoundFile with a filename. """
    self.fname = file
    self.loaded = False
    #self.load()
  def __repr__(self):
    return "[%s: %0.1fK %d]" % (self.fname, self.sr()/1000, self.samples().shape[1])
  def __iter__(self):
    return iter(self.samples()[0])
  def load(self):
    try:
      file = self.fname
      wav = wave.open(file)
      nsamples = wav.getnframes()
      self._sr = wav.getframerate()
      samplestring = wav.readframes(nsamples)
      self._samples = np.array([map(lambda x: float(ord(x)), list(samplestring))])
      wav.close()
    except Exception:
      self._sr = 0
      self._samples = np.array([[]], float)
    self.loaded = True
    return self
  def samples(self):
    if not self.loaded:
      self.load()
    return self._samples
  def sr(self):
    if not self.loaded:
      self.load()
    return self._sr

def LoadSpeech(directory):
  """ Recursively generate the *.wav files in a directory. """
  for root, dirs, files in os.walk(directory):
    for f in files:
      if re.search("\.wav$", f):
        yield SoundFile("%s/%s" % (root, f))
        #try:
        #  s = SoundFile(root + "/" + f)
        #  yield s
        #except Exception:
        #  pass

if __name__ == "__main__":
  for sound in itertools.islice(LoadSpeech("."), 10):
    print(sound)
