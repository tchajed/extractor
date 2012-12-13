from __future__ import print_function, division

from decorator import decorator
from libxtract import xtract
from collections import defaultdict
import swigtools
import math

def _feature(func, *args, **kw):
	""" Internal feature decorator.

	Handles memoization using the Extractor featurecache.
	func should:
	- be an instance method of Extractor
	- take a parameter t
	- depend only on t for correctness (for example, other parameters don't
		change within a time)
	"""
	# this is the required interface of the function signature
	self = args[0]
	featurecache = self._featurecache # created by the object initializer
	tspec = args[1]
	# the feature name
	fname = func.__name__
	# starting a new timestep
	if tspec in featurecache:
		cache = featurecache[tspec]
	else:
		cache = {}
		featurecache[tspec] = cache
	# cache now holds the specific values for this timestep
	if fname in cache:
		return cache[fname]
	else:
		cache[fname] = result = func(*args, **kw)
		return result

def feature(*factors):
	""" Decorate a method to make it a feature.

	Pass a list of window size multipliers the feature should be called at.

	- Handles registration of the function as a feature generator.
	- Sets up the cache.
	- passes most decoration work to _feature, which memoizes.
	"""
	# check that feature wasn't accidentally used as a parameter-less decorator
	if hasattr(factors, '__call__'):
		raise TypeError("feature needs a list of factors")
	factor_list = [f for f in factors]
	def feature_decorator(f):
		fn = decorator(_feature, f)
		fn._is_feature = True
		fn.factors = factor_list
		return fn
	return feature_decorator

def round_int(val, mult):
	return (val // mult) * mult

class Extractor:
	""" A feature extractor that wraps a soundfile. """
	def __init__(self, snd, cachesize=5):
		self.snd = snd
		self._featurecache = {}
		self._spectrumcache = {}
		self._samplecache = {}
		self.filtersize = size = 20
		class filterbank(defaultdict):
			def __missing__(self, window):
				self[window] = filters = xtract.create_filterbank(size, window)
				return filters
		self._mel_filters = filterbank()
	def getspectrum(self, tspec):
		""" Get the spectrum at a specific tspec.
		
		A tspec is a tuple (t, window). This considers the same time (in samples)
		different if used with different window sizes.
		"""
		return self._spectrumcache[tspec]
	def getsamples(self, tspec):
		""" Get the sample array at a specific tspec. """
		return self._samplecache[tspec]
	@feature(1)
	def Mean(self, tspec):
		spectrum = self.getspectrum(tspec)
		result, mean = xtract.xtract_mean(spectrum.a, len(spectrum), None)
		return mean
	@feature(1)
	def Stddev(self, tspec):
		spectrum = self.getspectrum(tspec)
		mean = self.Mean(tspec)
		result, var = xtract.xtract_variance(spectrum.a,
				len(spectrum),
				swigtools.args(mean))
		return math.sqrt(var)
	@feature(1)
	def Mfccs(self, tspec):
		spectrum = self.getsamples(tspec)
		filterbank = self._mel_filters[tspec[1]]
		mfccs = xtract.floatArray(self.filtersize)
		result = xtract.xtract_mfcc(spectrum.a, len(spectrum), filterbank, mfccs)
		return swigtools.CArray(mfccs, self.filtersize)
	def Features(self, minwindow):
		features = defaultdict(list)
		for name, method in self.__class__.__dict__.iteritems():
			if hasattr(method, "_is_feature"):
				for m in method.factors:
					features[m].append(method)
		f_array = defaultdict(list)
		for m in features.keys():
			window = m * minwindow
			nshift = window//2
			# helpful reference (along with formal argument names in src)
			# http://lists.create.ucsb.edu/pipermail/240/2008-May/001898.html
			xtract.xtract_init_mfcc(window, # block size
					self.snd.sr/2.0, # nyquist
					xtract.XTRACT_EQUAL_GAIN, # "style"
					80.0, 18000.0, # min/max frequency
					self.filtersize, # n_filters
					xtract.fft_tables(self._mel_filters[window])) # filter tables themselves
			for idx, (samples, spectrum) in enumerate(self.snd.spectrogram(window, nshift)):
				tspec = idx * nshift, window
				self._spectrumcache[tspec] = spectrum
				self._samplecache[tspec] = samples
				for feature in features[m]:
					vals = feature(self, tspec)
					try:
						f_array[tspec[0]].extend(vals)
					except TypeError:
						f_array[tspec[0]].append(vals)
		return [f_array[tspec] for tspec in sorted(f_array.keys())]


if __name__ == "__main__":
	from soundfile import LoadSpeech
	snd = LoadSpeech(".").next()
	e = Extractor(snd)
	features = e.Features(64)
	print(features)

