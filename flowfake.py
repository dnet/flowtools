#!/usr/bin/env python

from flow import Flow
from socket import socket, SO_REUSEADDR, SOL_SOCKET
from binascii import hexlify

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
		print 'Socket created:', address

	def __enter__(self):
		return self

	def __exit__(self, type, value, traceback):
		self.socket.close()

	def start(self):
		for s in self.init_socket():
			s.setblocking(1)
			for n, entry in enumerate(self.flow):
				if entry.direction == self.EXPECT:
					recvd = 0
					expected = len(entry.data)
					while recvd < expected:
						buf = s.recv(expected - recvd)
						if buf:
							recvd += len(buf)
							print '[{0:02d}-recv]'.format(n), hexlify(buf)
				elif entry.direction == self.SEND:
					print '[{0:02d}-send]'.format(n), hexlify(entry.data)
					s.send(entry.data)


class FakeServer(FakeSocket):
	EXPECT = Flow.SENT
	SEND = Flow.RECEIVED

	def init_socket(self):
		s = self.socket
		s.bind(self.address)
		s.listen(5)
		while True:
			sock, addr = s.accept()
			print 'Accepted connection from', addr
			yield sock


class FakeClient(FakeSocket):
	EXPECT = Flow.RECEIVED
	SEND = Flow.SENT

	def init_socket(self):
		self.socket.connect(self.address)
		yield self.socket


def print_usage():
	from sys import argv, stderr
	print >> stderr, "Usage: {0} (-s listen_port | -c connect_host connect_port) <filename>".format(argv[0])


if __name__ == '__main__':
	main()
