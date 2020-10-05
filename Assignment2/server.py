#!/usr/bin/python3

import socket 
import struct

# based on https://docs.python.org/3/howto/sockets.html

def doProtocol(clientsocket) :
	# read four bytes from the socket (1 padded int)
	receivedMessage = clientsocket.recv(4)

	# unpack and get the value from the received bytes
	chunk = struct.unpack("i", receivedMessage) # TODO: error check here
	value = chunk[0]
	print("server received: " + str(value))
	
	# pack and send a value one larger back
	sendMessage = struct.pack("i", value + 1)
	clientsocket.send(sendMessage)

def main() :
	# create an INET, STREAMing socket
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# bind the socket to a public host, and an arbitrary port
	serversocket.bind((socket.gethostname(), 9223))
	# become a server socket
	serversocket.listen(5)

	while True:
		# accept connections from outside
		(clientsocket, address) = serversocket.accept()
		doProtocol(clientsocket)
		clientsocket.close()
	
if __name__ == "__main__" :
	main()
