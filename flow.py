#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# flow.py - parses and represents a network flow
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

from binascii import unhexlify
from collections import namedtuple, defaultdict
import re

FLOW_ROW_RE = re.compile(r'^(\s*)([0-9a-f]+)\s+([0-9a-f\s]{1,49})', re.I)
NON_HEX_RE = re.compile(r'[^0-9a-f]', re.I)

class Flow(list):
	Entry = namedtuple('Entry', ['direction', 'data', 'offset'])
	SENT = 'sent'
	RECEIVED = 'received'
	DIRECTIONS = [SENT, RECEIVED]

	def __init__(self, filename, decode_func=None, frag_rules=None):
		with file(filename, 'r') as flow_file:
			list.__init__(self, load_flow(flow_file, decode_func))
		if frag_rules is not None:
			self.apply_rules(parse_frag_rules(frag_rules))
	
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

	def apply_rules(self, rules):
		for direction, dir_rules in rules.items():
			for rule in sorted(dir_rules):
				for index, entry in enumerate(self):
					if entry.direction.startswith(direction) and entry_has_pos(entry, rule):
						self.split_entry(index, rule)
						break

	def split_entry(self, index, pos):
		e = self[index]
		pos -= e.offset
		self[index] = self.Entry(direction=e.direction, offset=e.offset,
				data=e.data[:pos])
		self.insert(index + 1, self.Entry(direction=e.direction,
			offset=e.offset + pos, data=e.data[pos:]))

def entry_has_pos(entry, pos):
	if entry.offset > pos:
		return False
	return entry.offset + len(entry.data) > pos
	
def load_flow(flow_file, decode_func=None):
	offset_cache = {Flow.SENT: 0, Flow.RECEIVED: 0}
	wait_direction = None
	wait_offset = None
	wait_data = None
	d = decode_func if decode_func is not None else lambda x: x
	for m in filter(None, map(FLOW_ROW_RE.match, flow_file)):
		direction = Flow.SENT if m.group(1) == '' else Flow.RECEIVED
		offset = int(m.group(2), 16)
		data = unhexlify(NON_HEX_RE.sub('', m.group(3)))
		if wait_data is not None and wait_direction != direction:
			yield Flow.Entry(direction=wait_direction, data=d(wait_data), offset=wait_offset)
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
				yield Flow.Entry(direction=wait_direction, data=d(wait_data + data), offset=wait_offset)
				wait_data = None
			else:
				yield Flow.Entry(direction=direction, data=d(data), offset=offset)
	if wait_data is not None:
		yield Flow.Entry(direction=wait_direction, data=d(wait_data + data), offset=wait_offset)

def parse_frag_rules(rules):
	result = defaultdict(list)
	if rules is not None:
		for rule in rules.split(','):
			offset = rule[1:]
			result[rule[0]].append(int(offset[2:], 16)
				if offset.startswith('0x') else int(offset))
	return result
