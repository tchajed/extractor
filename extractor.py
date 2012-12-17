from __future__ import print_function, division
from multiprocessing import Pool, Lock
import numpy as np
import itertools
import random
import re
import soundfile
import sys
import os
import yaafelib as yf

class PhonemeLabeler:
	def __init__(self):
		pass
	def __call__(self, fname):
		""" Generate (timestamp, phoneme) tuples to label with phonemes. """
		phfname = re.sub("\.wav$", ".phn", fname)
		f = open(phfname)
		for line in f:
			start, _, ph = line.split(" ")
			start = int(start)
			ph = ph.strip()
			yield (start, ph)
		f.close()

def Labeler(f):
	""" Wrap the output of a function to make it a labeler.

	Converts a function that returns a single value for a file into the format expected by 
	"""
	def label_f(fname):
		return [(0, f(fname))]
	return label_f

def speaker(fname):
	""" Implements the speaker labelling function for TIMIT.
	
	The speaker is identified by (m|f)[a-z]{3}[0-9], where the first character is
	their gender, the three letters are their initials, and the number
	disambiguates speakers with identical initials. This is simply the name of
	the directory that holds the wav file in the TIMIT database.
	"""
	dirs = fname.split("/")
	if len(dirs) < 2:
		return ""
	return dirs[-2]

class Extractor:
	""" Extract features according to a plan over many sound files. """
	def __init__(self, fp, labeler):
		""" Instantiate an extractor with a feature plan and labeler.

		A feature plan is a prepared set of features from yaafe.

		A labeler is an object that will be called with a filename and should
		return a generator of tuples (sample, label), where the label applies to
		the audio data between sample and the next tuple. The first tuple's
		timestamp is ignored. Note that this means every timestep will be given a
		label and a single label for the entire file can be implemented by
		returning a list with one tuple whose second element is the desired label.
		The function Labeler allows to create a valid labeler with a simpler
		function that just outputs any label value.
		
		"""
		self.fp = fp
		self.labeler = labeler
		self.engine = yf.Engine()
		self.engine.load(fp.getDataFlow())
		minstep = sys.maxint
		for feat, info in self.engine.getOutputs().iteritems():
			minstep = min(info['sampleStep'], minstep)
		self._minstep = minstep
		self._indexf = {}
		def linear(domainmax, rangemax):
			def transform(i):
				return int(i * domainmax / rangemax)
			return transform
		for feat, info in self.engine.getOutputs().iteritems():
			step = info['sampleStep']
			# a function that maps the minstep indices to indices for a particular
			# feature. Longer steps have fewer indices, so many minstep indices will
			# map to the same value here, resulting in repetition.
			self._indexf[feat] = linear(minstep, step)
	def features(self, sound):
		""" Execute the plan for a given sound, returning a time series of vector data. """
		features = []
		feats = self.engine.processAudio(sound.samples())
		labels = [l for l in self.labeler(sound.fname)]
		# make a pseudo-label past the end of the sound
		labels.append( (sound.samples().shape[1] + 1, None) )
		# the current label index
		currl = 0
		for i,t in enumerate(xrange(0, sound.samples().shape[1], self._minstep)):
			# make sure the next time is the one just past the current label
			while t > labels[currl+1][0]:
				currl += 1
			currlabel = labels[currl][1]
			# start out features with the label for this timestep
			features.append([currlabel])
			for feat, vals in feats.iteritems():
				index = self._indexf[feat](i)
				features[i].extend(vals[index])
		return features
			
if __name__ == "__main__":
	if len(sys.argv) > 1:
		rootdir = sys.argv[1]
	else:
		rootdir = "."
	fp = yf.FeaturePlan(sample_rate=16000)
	fp.addFeature('mfcc: MFCC blockSize=512 stepSize=256')
	fp.addFeature('mfcc_d1: MFCC blockSize=512 stepSize=256 > Derivate DOrder=1')
	fp.addFeature('sss: SpectralShapeStatistics blockSize=512 stepSize=256')

	l = Lock() # a printing lock
	def extract(sounds):
		e = Extractor(fp, Labeler(speaker))
		sound_features = []
		for sound in sounds:
			sound_features.append(e.features(sound))
			#print(sound)
			#print(np.array(features).shape)
		l.acquire()
		for sound_ft in sound_features:
			for feature_vec in sound_ft:
				print(",".join([str(f) for f in feature_vec]))
		l.release()
		return None
	sounds = [s for s in itertools.islice(soundfile.LoadSpeech(rootdir), 5000)]
	random.shuffle(sounds)
	sounds = sounds[:500]
	p = Pool(4)
	n = 50
	p.map(extract, [sounds[i:i+n] for i in xrange(0, len(sounds), n)])
