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

