Created by Aaron Zehm, amz52

Aaron's FTP Server

This ftp server takes 2 arguements. The first is the name of the log file and
the second is the port to have the server run on.

for example:
python ftpserver.py testing.log 2121

username and password are stored in a text file called users.txt

logs are created with each session of the server running and will make
a new file if a file is present already in the current directory

V0.2 --  Assignment 4 updates

Added recording for individual connections to compare with server side records as way to check against
malicious connections.

Added SSL to data connections and commands allowing for encryption.

