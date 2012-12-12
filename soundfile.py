#!/usr/bin/env python
# vim: tw=80:ts=2:sw=2:et:sta

from __future__ import print_function
from libxtract import xtract
import itertools
import os
import re
import swigtools
import wave

class SoundFile:
  def __len__(self):
    return self.nsamples
  def __init__(self, file):
    """
    Instantiate a SoundFile with a filename.

    Stores the samples of the file in a floatArray for immediate use.
    """
    self.fname = file
    wav = wave.open(file)
    self.nsamples = wav.getnframes()
    self.sr = wav.getframerate()
    samplestring = wav.readframes(self.nsamples)
    data = map(ord, list(samplestring))
    # convert samples to a floatArray
    a = xtract.floatArray(self.nsamples)
    for i in xrange(self.nsamples):
      a[i] = float(data[i])
    self.samples = a
  def spectrogram(self, nfft, nshift):
    """ Generate spectral vectors from the sound samples.

    nfft: length of the Fourier window
    nshift: the number of samples to shift by between spectra
    """
    start = 0
    end = start + nfft
# initialize the internal fft plan
    xtract.xtract_init_fft(nfft, xtract.XTRACT_SPECTRUM)
    args = xtract.floatArray(4)
    args[0] = float(self.sr) / float(nfft)
    args[1] = xtract.XTRACT_LOG_POWER_SPECTRUM
    args[2] = 0 # 0/1: whether or not to include DC component
    args[3] = 0 # 0/1: whether or not to apply normalization to the result
    while end <= len(self):
      input = xtract.floata_index(self.samples, start)
# increase to nfft + 2 if including DC component
      spectrum = xtract.floatArray(nfft) 
      result = xtract.xtract_spectrum(input,
          nfft,
          xtract.floata_to_voidp(args),
          spectrum)
      # first nfft/2 floats are coefficients, second half are just frequencies
      yield spectrum
      start += nshift
      end += nshift

def LoadWaves(directory):
  """ Recursively generate the *.wav files in a directory. """
  for root, dirs, files in os.walk(directory):
    for f in files:
      if re.search("\.wav$", f):
        yield SoundFile(root + "/" + f)

if __name__ == "__main__":
  def at(it, n):
    l = list(itertools.islice(it, n, n+1))
    if len(l) > 0:
      return l[0]
    else:
      return None
  def print_floata(a, n):
    for i in xrange(0,n):
      print(a[i], ", ", end="", sep="")
    print("\n")
  wav = at(LoadWaves("."), 0)
  print(len(wav))
#sr = swigtools.floatPtr(wav.sr)
# pass xtract.floata_to_voidp(sr)
#xtract.xtract_init_fft(len(wav), xtract.XTRACT_SPECTRUM)
  result, mean = xtract.xtract_mean(wav.samples, len(wav), None)
  print(mean)
  print(wav.fname)
  for spectra in wav.spectrogram(1024, 256):
    print_floata(spectra, 10)
