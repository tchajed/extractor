from soundfile import SoundFile
from decorator import decorator
from collections import deque
from libxtract import xtract

class Cache:
	""" A simple cache that replaces oldest-first. """
	def __init__(self, cap):
		self.cap = cap
		self._cache = {}
		self._keys = deque([])
	def __getitem__(self, key):
		return self._cache[key]
	def __setitem__(self, key, val):
		self._keys.append(key)
		self._cache[key] = val
		# do we need to evict?
		if len(self._cache) > self.cap:
			# eviction policy is simply to remove oldest added key
			# so add them in order!
			toremove = self._keys.popleft()
			del self._cache[toremove]
	def __contains__(self, item):
		return item in self._cache

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
	t = args[1]
	# the feature name
	fname = func.__name__
	# starting a new timestep
	if t in featurecache:
		cache = featurecache[t]
	else:
		# for a given time, feature values are cached without resource limits
		cache = {}
		featurecache[t] = cache
	# cache now holds the specific values for this timestep
	if fname in cache:
		return cache[fname]
	else:
		cache[fname] = result = func(args, kw)
		return result

def feature(f):
	""" Decorate a method to make it a feature.

	- Handles registration of the function as a feature generator.
	- Sets up the cache.
	- passes most decoration work to _feature, which memoizes.
	"""
	fn = decorator(_feature, f)
	fn._is_feature = True
	return fn

class Extractor:
	""" A feature extractor that wraps a soundfile. """
	def __init__(self, snd, cachesize=5):
		self.snd = snd
		self._featurecache = Cache(cachesize)
		self._spectrumcache = Cache(cachesize)
	def getspectrum(self, t):
		""" Get the spectrum at a specific time (in samples). """
		return self._spectrumcache[t]
	@feature
	def Mean(self, t):
		spectrum = self.getspectrum(t)
		result, mean = xtract.xtract_mean(spectrum.a, len(spectrum), None)
		return mean
