#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# flowfake.py - fakes a server or a client based on a Flow object
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

from __future__ import print_function
from flow import Flow
from socket import socket, SO_REUSEADDR, SOL_SOCKET
from binascii import hexlify
from ui import COLORS, horizontal_separator

def main():
	from sys import argv
	if '-h' in argv:
		return print_usage()
	try:
		mode = argv[1]
		if mode == '-s':
			proto = FakeServer
			address = ('', int(argv[2]))
			filename = argv[3]
		elif mode == '-c':
			proto = FakeClient
			address = (argv[2], int(argv[3]))
			filename = argv[4]
		else:
			raise ValueError('Invalid mode')
	except (ValueError, IndexError):
		print_usage()
		raise SystemExit(1)
	else:
		flow = Flow(filename)
		with proto(flow, address) as fake:
			fake.start()


class FakeSocket(object):
	def __init__(self, flow, address):
		self.flow = flow
		self.socket = socket()
		self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		self.address = address
		print('Socket created:', address)

	def __enter__(self):
		return self

	def __exit__(self, type, value, traceback):
		self.socket.close()

	def start(self):
		diff = COLORS[2]
		for s in self.init_socket():
			s.setblocking(1)
			for n, entry in enumerate(self.flow):
				horizontal_separator()
				if entry.direction is self.EXPECT:
					recvd = 0
					expected = len(entry.data)
					entry_header(n, 'xpct', 1, entry.data)
					entry_header(n, 'recv', 2)
					while recvd < expected:
						buf = s.recv(1)
						if buf:
							print(diff(hexlify(buf)) if buf != entry.data[recvd] else '..', end='')
							recvd += len(buf)
						else:
							break
					print('')
				elif entry.direction is self.SEND:
					entry_header(n, 'send', 0, entry.data)
					s.send(entry.data)
			horizontal_separator()


def entry_header(num, title, color, data=None):
	c = COLORS[color]
	print('[{0:02d}-{1}]'.format(num, c(title)), end=' ')
	if data:
		print(c(hexlify(data)))


class FakeServer(FakeSocket):
	EXPECT = Flow.SENT
	SEND = Flow.RECEIVED

	def init_socket(self):
		s = self.socket
		s.bind(self.address)
		s.listen(5)
		while True:
			print('Listening...')
			sock, addr = s.accept()
			print('Accepted connection from', addr)
			yield sock


class FakeClient(FakeSocket):
	EXPECT = Flow.RECEIVED
	SEND = Flow.SENT

	def init_socket(self):
		self.socket.connect(self.address)
		yield self.socket


def print_usage():
	from sys import argv, stderr
	print("Usage: {0} (-s listen_port | -c connect_host connect_port) <filename>".format(argv[0]),
			file=stderr)


if __name__ == '__main__':
	main()
