# vim: tw=80:ts=2:sw=2:et:sta
"""
Wrapper for sound files that provides the low-level spectrogram.

"""

from __future__ import print_function
from libxtract import xtract
import itertools
import os
import re
import swigtools
import sys
import wave

class SoundFile:
  def __len__(self):
    return len(self.samples)
  def __init__(self, file):
    """
    Instantiate a SoundFile with a filename.

    Stores the samples of the file in a floatArray for immediate use.
    """
    self.fname = file
    wav = wave.open(file)
    nsamples = wav.getnframes()
    self.sr = wav.getframerate()
    samplestring = wav.readframes(nsamples)
    data = map(ord, list(samplestring))
    # convert samples to a floatArray
    a = xtract.floatArray(nsamples)
    for i in xrange(nsamples):
      a[i] = float(data[i])
    self.samples = swigtools.CArray(a, nsamples)
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
      input = xtract.floata_index(self.samples.a, start)
# increase to nfft + 2 if including DC component
      spectrum = xtract.floatArray(nfft) 
      result = xtract.xtract_spectrum(input,
          nfft,
          xtract.floata_to_voidp(args),
          spectrum)
      # TODO: check result to catch errors
      # first nfft/2 floats are coefficients, second half are just frequencies
      yield spectrum
      start += nshift
      end += nshift

def LoadSpeech(directory):
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
  sound = at(LoadSpeech("."), 0)
  if sound is None:
    print("no wav files found")
    sys.exit(1)
  print(len(sound))
  sr = swigtools.args(sound.sr)
#xtract.xtract_init_fft(len(wav), xtract.XTRACT_SPECTRUM)
  result, mean = xtract.xtract_mean(sound.samples.a, len(sound), None)
  print(mean)
  print(sound.fname)
  for spectra in sound.spectrogram(1024, 256):
    print_floata(spectra, 10)
