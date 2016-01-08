#!/usr/bin/env python

from ui import COLORS
from flow import Flow
from flowdiff import diff_flows
from itertools import izip
from sys import argv

class FileEntry(object):
	offset = 0
	direction = Flow.RECEIVED

	def __init__(self, filename):
		with file(filename) as f:
			self.data = f.read()

def main():
	filenames = argv[1:]
	diff_flows([[FileEntry(fn)] for fn in filenames])
	print 'Input files:'
	for color, fn in izip(COLORS, filenames):
		print ' - ' + color(fn)

if __name__ == '__main__':
	main()
