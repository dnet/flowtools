#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# flowdiff.py - shows differences between Flow objects
#
# Copyright (c) 2013 András Veres-Szentkirályi
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

from flow import Flow
from itertools import islice, chain
from operator import attrgetter
from binascii import hexlify
from ui import COLORS, horizontal_separator, width, print_input_filenames

def diff_flows(flows, skip_offset=None, max_entries=None, fix_diff_treshold=5):
	if skip_offset is not None:
		flows = (f.filter_by_offset(skip_offset) for f in flows)
	for entry_no, entries in enumerate(zip(*flows)):
		if max_entries is not None and entry_no == max_entries:
			break

		entries_bytes = tuple(tuple(data) for data in map(attrgetter('data'), entries))
		lengths = set(map(len, entries_bytes))
		print('[i] E{entry_no} // {dirs} // Offset: {offsets} // Length: {lens}'.format(
				entry_no=entry_no,
				offsets=sorted(set(e.offset for e in entries)),
				dirs='/'.join(sorted(set(
					COLORS[Flow.DIRECTIONS.index(e.direction)](e.direction)
					for e in entries))),
				lens=sorted(lengths)))

		min_len = min(lengths)
		first_data = entries_bytes[0]
		common_bytes = [n for n in range(min_len) if all(e[n] == first_data[n] for e in entries_bytes[1:])]
		enum_izip_entries_bytes = tuple(enumerate(zip(*entries_bytes)))
		
		if len(lengths) > 1:
			look_for_length_byte(entries_bytes, enum_izip_entries_bytes)
			for match_len in range(min_len - 1, 0, -1):
				fd_match = first_data[-match_len:]
				if all(e[-match_len:] == fd_match for e in entries_bytes[1:]):
					print('[i] Common postfix: {0}'.format(':'.join(
						COLORS[len(Flow.DIRECTIONS)]('{0:02x}'.format(c)) for c in fd_match)))
					break

		all_same = (len(set(entries_bytes)) == 1)
		if all_same:
			entries = (entries[0],)
		elif fix_diff_treshold:
			look_for_fix_diff(len(entries), enum_izip_entries_bytes, fix_diff_treshold)
		else:
			print('[i] (ignoring patterns)')

		blobs = [entry.data for entry in entries]
		for i, data in enumerate(blobs):
			print()
			hexdump, asciidump = ([(empty if (n in common_bytes and i) else COLORS[
				next(bi for bi, bd in enumerate(blobs) if len(bd) >= n + 1 and
					bd[n] == c)](conv(bytes([c])).decode('ascii')))
				for n, c in enumerate(data)] for empty, conv in
				(('..', hexlify), ('.', asciify)))
			bytes_per_line = (width - (1 + 8 + 2 + 2)) // 17 * 4
			for offset in range(0, len(data), bytes_per_line):
				print('{offset:08x}  {hex}  {ascii}'.format(offset=offset,
					hex='  '.join(' '.join(padspace(hexdump[do:do + 4], 4))
						for do in range(offset, offset + bytes_per_line, 4)),
					ascii=''.join(asciidump[offset:offset + bytes_per_line])))
	
		if all_same:
			print('(all entries are the same)')

		horizontal_separator()

def padspace(data: bytes, length: int):
	return data if len(data) >= length else chain(data, ['  '] * (length - len(data)))

def asciify(bytestr: bytes) -> bytes:
	return bytestr if 0x20 <= bytestr[0] <= 0x7e else b'.'

def look_for_length_byte(entries, enum_izip_entries_bytes):
	for i, pos_bytes in enum_izip_entries_bytes:
		diffs = set(b - len(e) for e, b in zip(entries, pos_bytes))
		if len(diffs) == 1:
			diff = abs(next(iter(diffs)))
			print('[i] Possible length byte at offset 0x{0:02x}, diff = {1}'.format(i, diff))

def look_for_fix_diff(entries_num, enum_izip_entries_bytes, treshold: int):
	pos_bytes_range = list(range(1, entries_num))
	printed = 0
	for i, pos_bytes_1 in enum_izip_entries_bytes:
		if len(set(pos_bytes_1)) == 1:
			continue
		for j, pos_bytes_2 in islice(enum_izip_entries_bytes, i):
			diff = pos_bytes_1[0] - pos_bytes_2[0]
			for k in pos_bytes_range:
				if pos_bytes_1[k] - pos_bytes_2[k] != diff:
					break
			else:
				if printed == treshold:
					print(('[i] (there are more patterns, but only the first '
						'{1} shown)').format(treshold, str(treshold) + ' entries are'
								if treshold > 1 else 'entry is'))
					return
				di, dj = ('0x{0:02x} [{1}]'.format(pos, ' '.join(c('{0:02x}'.format(v))
						for c, v in zip(COLORS, values)))
						for pos, values in ((i, pos_bytes_1), (j, pos_bytes_2)))
				fmt = ('[i] difference between bytes {0} and {1} is always {2}'
						if diff else '[i] bytes {0} and {1} always match')
				print(fmt.format(di, dj, abs(diff)))
				printed += 1

def main():
	from argparse import ArgumentParser
	parser = ArgumentParser(description='Diff tool for Wireshark TCP flows')
	parser.add_argument('flow', nargs='+', help='flow files')
	parser.add_argument('-m', '--max-entries', metavar='N', type=int,
			help='displays only the first N flow entries')
	parser.add_argument('-s', '--skip-sent-bytes', metavar='N', type=int,
			help='ignores sent flow entries with an offset lower than N')
	parser.add_argument('-r', '--skip-recv-bytes', metavar='N', type=int,
			help='ignores received flow entries with an offset lower than N')
	parser.add_argument('-d', '--decode-function', metavar='foo.bar',
			help='applies bar() from module foo to all data for decoding')
	parser.add_argument('-t', '--fix-diff-treshold', metavar='N', type=int,
			help='displays only the first N patterns (fix diff + match)', default=5)
	parser.add_argument('-f', '--manual-fragmentation', metavar='rules',
			help='fragment packets at manual boundaries (see README)')
	args = parser.parse_args()

	skip_offset = {}
	if args.skip_sent_bytes:
		skip_offset[Flow.SENT] = args.skip_sent_bytes
	if args.skip_recv_bytes:
		skip_offset[Flow.RECEIVED] = args.skip_recv_bytes
	if args.decode_function:
		mod_name, func_name = args.decode_function.split('.')
		decode_func = getattr(__import__(mod_name), func_name)
	else:
		decode_func = None
	flows = [Flow(fn, decode_func=decode_func,
		frag_rules=args.manual_fragmentation) for fn in args.flow]
	diff_flows(flows, skip_offset=skip_offset, max_entries=args.max_entries,
			fix_diff_treshold=args.fix_diff_treshold)
	print_input_filenames(args.flow)

def print_usage():
	from sys import argv, stderr
	print("Usage: {0} [-m max_entries] [-s skip_sent_bytes] [-r skip_recvd_bytes] [-d decode_function] <filename> ...".format(argv[0]), file=stderr)

if __name__ == '__main__':
	main()
