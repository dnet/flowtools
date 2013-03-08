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
from itertools import imap, ifilter
from collections import namedtuple
import re

FLOW_ROW_RE = re.compile(r'^(\s*)([0-9a-f]+)\s+([0-9a-f\s]{1,49})', re.I)
NON_HEX_RE = re.compile(r'[^0-9a-f]', re.I)

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

