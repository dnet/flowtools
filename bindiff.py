#!/usr/bin/env python

from ui import print_input_filenames
from flow import Flow
from flowdiff import diff_flows
from sys import argv

class FileEntry(object):
	offset = 0
	direction = Flow.RECEIVED

	def __init__(self, filename):
		with open(filename, 'rb') as f:
			self.data = f.read()

def main():
	filenames = argv[1:]
	diff_flows([[FileEntry(fn)] for fn in filenames])
	print_input_filenames(filenames)

if __name__ == '__main__':
	main()
