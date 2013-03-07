#!/usr/bin/env python

from binascii import unhexlify
from itertools import imap, ifilter, izip
from collections import namedtuple
from blessings import Terminal
import re

FLOW_ROW_RE = re.compile(r'^(\s*)([0-9a-f]+)\s+([0-9a-f\s]{1,49})', re.I)
NON_HEX_RE = re.compile(r'[^0-9a-f]', re.I)

T = Terminal()
COLORS = [T.cyan, T.green, T.yellow, T.red]

class Flow(list):
	Entry = namedtuple('Entry', ['direction', 'data', 'offset'])
	SENT = 'sent'
	RECEIVED = 'received'
	DIRECTIONS = [SENT, RECEIVED]

	def __init__(self, filename):
		with file(filename, 'r') as flow_file:
			list.__init__(self, load_flow(flow_file))
	
	def filter_by_offset(self, skip_offset):
		passed = set()
		n = 0
		for n, i in enumerate(self):
			d = i.direction
			if d not in passed:
				offset = skip_offset.get(d)
				if offset is not None and i.offset >= offset:
					passed.add(d)
			if len(passed) == len(skip_offset):
				break
		return self[n:]
	
def load_flow(flow_file):
	offset_cache = {Flow.SENT: 0, Flow.RECEIVED: 0}
	wait_direction = None
	wait_offset = None
	wait_data = None
	for m in ifilter(None, imap(FLOW_ROW_RE.match, flow_file)):
		direction = Flow.SENT if m.group(1) == '' else Flow.RECEIVED
		offset = int(m.group(2), 16)
		data = unhexlify(NON_HEX_RE.sub('', m.group(3)))
		if wait_data is not None and wait_direction != direction:
			yield Flow.Entry(direction=wait_direction, data=wait_data, offset=wait_offset)
			wait_data = None
		last_offset = offset_cache[direction]
		assert last_offset == offset
		offset_cache[direction] = last_offset + len(data)
		if len(data) == 16:
			if wait_data is None:
				wait_direction = direction
				wait_offset = offset
				wait_data = data
			else:
				wait_data += data
		else:
			if wait_data is not None:
				yield Flow.Entry(direction=wait_direction, data=wait_data + data, offset=wait_offset)
				wait_data = None
			else:
				yield Flow.Entry(direction=direction, data=data, offset=offset)

def diff_flows(flows, skip_offset=None, max_entries=None):
	for entry_no, entries in enumerate(izip(*(flows if skip_offset is None
			else (f.filter_by_offset(skip_offset) for f in flows)))):
		if max_entries is not None and entry_no == max_entries:
			break

		lengths = set(len(e.data) for e in entries)
		print '[i] E{entry_no} // {dirs} // Offset: {offsets} // Length: {lens}'.format(
				entry_no=entry_no,
				offsets=sorted(set(e.offset for e in entries)),
				dirs='/'.join(sorted(set(
					COLORS[Flow.DIRECTIONS.index(e.direction)](e.direction)
					for e in entries))),
				lens=sorted(lengths))

		min_len = min(lengths)
		first_data = entries[0].data
		common_bytes = [n for n in xrange(min_len) if all(e.data[n] == first_data[n] for e in entries[1:])]
		
		if len(lengths) > 1:
			for i in xrange(min_len):
				diffs = set(ord(e.data[i]) - len(e.data) for e in entries)
				if len(diffs) == 1:
					diff = abs(next(iter(diffs)))
					print '[i] Possible length byte at offset {0}, diff = {1}'.format(i, diff)
			for match_len in xrange(min_len - 1, 0, -1):
				fd_match = first_data[-match_len:]
				if all(e.data[-match_len:] == fd_match for e in entries[1:]):
					print '[i] Common postfix: {0}'.format(':'.join(
						COLORS[len(Flow.DIRECTIONS)]('{0:02x}'.format(ord(c))) for c in fd_match))
					break

		all_same = (len(set(e.data for e in entries)) == 1)
		if all_same:
			entries = (entries[0],)

		for i, entry in enumerate(entries):
			print ''
			print ' '.join(('..' if (n in common_bytes and i) else COLORS[
				next(bi for bi, be in enumerate(entries) if len(be.data) >= n + 1 and
					be.data[n] == c)]('{0:02x}'.format(ord(c))))
				for n, c in enumerate(entry.data))
	
		if all_same:
			print '(all entries are the same)'

		print T.bold_black('-' * (T.width - 1))

def main():
	from sys import argv
	n = 1
	filenames = []
	skip_offset = {}
	max_entries = None
	try:
		while n < len(argv):
			arg = argv[n]
			if arg == '-m':
				n += 1
				max_entries = int(argv[n])
			elif arg == '-s':
				n += 1
				skip_offset[Flow.SENT] = int(argv[n])
			elif arg == '-r':
				n += 1
				skip_offset[Flow.RECEIVED] = int(argv[n])
			else:
				filenames.append(arg)
			n += 1
	except (ValueError, IndexError):
		print_usage()
		raise SystemExit(1)
	else:
		flows = [Flow(fn) for fn in filenames]
		diff_flows(flows, skip_offset=skip_offset, max_entries=max_entries)
		print 'Input files:'
		for n, fn in enumerate(filenames):
			print ' - ' + COLORS[n](fn)

def print_usage():
	from sys import argv, stderr
	print >> stderr, "Usage: {0} [-m max_entries] [-s skip_sent_bytes] [-r skip_recvd_bytes] <filename> ...".format(argv[0])

if __name__ == '__main__':
	main()
