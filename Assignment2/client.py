#!/usr/bin/python3

# based on https://docs.python.org/3/howto/sockets.html

from A4 import logger

import socket
import struct
import sys
import os
import datetime

BUFFER_SIZE = 1024
commands = ['USER', 'PASS', 'CWD', 'QUIT', 'PASV', 'EPSV', 'PORT',
			'EPRT', 'RETR', 'STOR', 'PWD', 'SYST', 'LIST', 'HELP']

class ftpSocket:

	def __init__(self, host, logger, port):
		self.hostIP = host
		self.logger = logger
		self.port = port
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.bind((self.hostIP, self.port))
		self.socket.settimeout(30)

	def connect(self, port=21):
		response = None
		try:
			# self.logger.log("Attempting to connect...")
			self.socket.connect((self.hostIP, self.port))
			response = self.socket.recv(BUFFER_SIZE)
			# self.logger.log("Connection successful (" + self.hostIP + " port " + str(self.port) + ")")
			print("Connection successful (" + self.hostIP + " port " + str(self.port) + ")")
		except Exception as e:
			# self.logger.log("Error connecting: " + str(e))
			print("Not connected")
		# self.logger.log("Server Response: " + response.rstrip())
		return response

	# def doProtocol(sock):
	# 	value = int(sys.argv[1])
	#
	# 	# pack and send our argument
	# 	data = struct.pack("i", value)
	# 	sock.send(data)
	#
	# 	# get back a response and unpack it
	# 	receivedmessage = sock.recv(4)
	# 	chunk = struct.unpack("i", receivedmessage)
	# 	# take the first int only
	# 	message = chunk[0]
	#
	# # print("client received: " + str(message))

	@staticmethod
	def checkIP():
		try:
			socket.inet_aton(str(sys.argv[1]))
			address = sys.argv[1]
		except socket.error:
			try:
				socket.gethostbyname(sys.argv[1])
				address = sys.argv[1]
			except socket.gaierror:
				print('Not a valid host')
				sys.exit()
		return address


	def Logger(self):
		filename = sys.argv[2]
		if os.path.isfile(filename) is True:
			logfile = open(filename, 'a+')



def main():
	if len(sys.argv) > 2 and len(sys.argv) < 4:
		host = sys.argv[1]
		logfile = sys.argv[2]
		port = 21
	elif len(sys.argv) == 4:
		host = sys.argv[1]
		logfile = sys.argv[2]
		port = sys.argv[3]
	else:
		print('Error: Required arguments not sufficient')

	address = ftpSocket.checkIP()
	ftpSocket.connect(sys.argv[2])




	# if sys.agrv[1].isdigit():
	# 	address = sys.argv[1]
	# else:
	# 	address = socket.gethostbyname(sys.argv[1])
	# print(address)

	# if len(sys.argv) != 2 or not sys.argv[1].isdigit():
	# 	print(sys.argv)
	# 	print("Usage: " + str(sys.argv[0]) + " <int>")
	# 	exit(1)

	# create an INET, STREAMing socket
	# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# # now connect to the web server on port 9223, which we've made our server listen to
	# # change the hostname if not on the same server
	# sock.connect((socket.gethostname(), 9223))
	# doProtocol(sock)
	# sock.close()


if __name__ == "__main__":
	main()
