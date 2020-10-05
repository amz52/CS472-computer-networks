Created by Aaron Zehm, amz52

Aaron's FTP Server

This ftp server takes 2 arguements. The first is the name of the log file and
the second is the port to have the server run on.

for example:
python ftpserver.py testing.log 2121

username and password are stored in a text file called users.txt

logs are created with each session of the server running and will make
a new file if a file is present already in the current directory

