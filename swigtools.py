from libxtract import xtract

f = xtract.floatArray(1)

def floatPtr(val):
	f[0] = float(val)
	return f
