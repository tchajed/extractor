# vim: tw=80:ts=2:sw=2:et:sta
"""
Wrapper for sound files.

"""

from __future__ import print_function
from libxtract import xtract
import itertools
import os
import re
import swigtools
import sys
import wave
import numpy as np

class SoundFile:
  def __len__(self):
    return len(self.samples)
  def __init__(self, file):
    """
    Instantiate a SoundFile with a filename.

    Stores the samples of the file.
    """
    self.fname = file
    wav = wave.open(file)
    nsamples = wav.getnframes()
    self.sr = wav.getframerate()
    samplestring = wav.readframes(nsamples)
    self.samples = np.array([map(lambda x: float(ord(x)), list(samplestring))])
  def __repr__(self):
    return "[%s: %0.1fK %d]" % (self.fname, self.sr/1000, self.samples.shape[1])
  def __iter__(self):
    return iter(self.samples[0])

def LoadSpeech(directory):
  """ Recursively generate the *.wav files in a directory. """
  for root, dirs, files in os.walk(directory):
    for f in files:
      if re.search("\.wav$", f):
        yield SoundFile(root + "/" + f)

if __name__ == "__main__":
  for sound in itertools.islice(LoadSpeech("."), 10):
    print(sound)
