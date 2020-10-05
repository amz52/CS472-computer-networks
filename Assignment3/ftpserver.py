import os
import sys
import socket
import threading
from copy import deepcopy
from datetime import datetime
# -*- coding: utf-8 -*-


"""
The Server class handles the construction of the beginning and end of the server. It takes the port number and the log
file that the server will use for that session. It also checks to see if the users list file is present in the same
directory and sets the modes for port mode and pasv mode.
"""


class Server:
    def __init__(self, port, logger):
        self.port = port
        self.record = logger
        self.cwd = os.getcwd()

        self.usersfile = self.cwd + '\\users.txt'
        self.pasvmode = 'ON'
        self.portmode = 'OFF'

        self.authenticated = None

        if not os.path.isfile(self.usersfile):
            print('Error: Username file not in current directory.')
            sys.exit(1)
        elif self.pasvmode == 'NO' and self.portmode == 'NO':
            print('Error: Both PASV and PORT modes are disabled. Cannot proceed.')
            sys.exit(1)

        self.serversocket = FtpSocket(self.port, self.record)
        self.clientle = []

    def ignition(self):
        self.serversocket.listen()
        while True:
            connection, address = self.serversocket.accept()
            thread = Thread(connection, address, self.record, self)
            thread.daemon = True
            thread.start()

    def halt(self):
        self.serversocket.close()
        self.record.log('Server halted. Closing down connection')

    # def conf(self, configfile):
    #     with open('server.conf', 'r') as file:
    #         settings = file.readlines()
    #
    #     print('Reading config settings.')
    #     for line in settings:
    #         values = line.split(':')
    #         if values[0] == 'PASV':
    #             if values[1].rstrip() is None:
    #                 self.PASV = 'ON'
    #             else:


"""
The Thread class handles each instance of when a user connects to the server and handles that specific thread.
It takes the connection object and address that is created once a connection with the user is established. It 
also takes the logger that is created and inherits the Server class. It also manages the execution of commands
received by the client.
"""


class Thread:

    def __init__(self, connection, address, logger, server):
        self.connection = connection
        self.address = address
        self.record = logger
        self.server = server

        self.user_variable = None
        self.password = None
        self.user_status = False
        self.PASV = False

        self.server_socket = None
        self.data_socket = None
        self.data_address = None
        self.data_port = None

        self.attempts = 0
        self.state = StateMachine(self.connection, self.address)
        self.commands = ['CDUP', 'CWD', 'EPRT', 'EPSV', 'HELP', 'LIST', 'PASS',
                         'PASV', 'PORT', 'PWD', 'QUIT', 'RETR', 'USER']
        # super(Thread, self).__init__()

    def start(self):
        """
        Where most of the action happens and processes the responses from the server and client are processed.
        """
        self.record.log('Starting Server')
        self.connection.sendall(b'220 Welcome to my FTP Server\n')
        option = 'null'

        while True:
            try:
                response = self.connection.recv(512)
                response = str(response.decode().rstrip())
                if 'UTF' in response:
                    self.connection.sendall(b'202 Command not supported, UTF8 mode enabled by default.\n')
            except Exception as e:
                self.record.log('Connection lost or aborted with Error: ' + str(e))
                break
            if not response:
                self.record.log('No response...')
                break
            else:
                arguments = response.split(' ')
                command = arguments[0]
                command = command.rstrip()
                if len(arguments) > 1:
                    option = arguments[1]
                    option = option.rstrip()

                self.record.log('Processing ' + response + '...')
                if self.valid_command(command):
                    if command == 'PORT':
                        if self.server.portmode.rstrip() == 'NO':
                            self.connection.sendall(b'Error: PORT Mode disabled.\n')
                            continue

                    if command == 'PASV':
                        if self.server.pasvmode.rstrip() == 'NO':
                            self.connection.sendall(b'Error: PASV Mode disabled.\n')
                            continue

                    if command == 'QUIT':
                        break

                    successful = self.execution(command, option)
                    self.state.update(command, successful[1])
                    self.connection.sendall(successful[0].encode())
                if not self.valid_command(command) and command != 'OPTS':
                    self.connection.sendall(('202 Command ' + command + ' not supported.\n').encode())

        self.connection.sendall(b'Thank you for using the FTP server. Good Bye <3\n')
        self.record.log('Thread closed')
        self.connection.close()

    def valid_command(self, command):
        """
        Checks if the command given is in the list of approved commands
        """
        command = command.split(' ')[0]
        if command in self.commands:
            return True
        else:
            return False

    def execution(self, command, option):
        """
        Executes the command once it has been verified and returns the results
        """
        if command == self.commands[0]:
            return self.CDUP()
        if command == self.commands[1]:
            return self.CWD(option)
        if command == self.commands[2]:
            return self.EPRT(option)
        if command == self.commands[3]:
            return self.EPSV()
        if command == self.commands[4]:
            return self.HELP()
        if command == self.commands[5]:
            if option is None:
                option = '.'
            return self.LIST(option)
        if command == self.commands[6]:
            return self.PASS(option)
        if command == self.commands[7]:
            return self.PASV()
        if command == self.commands[8]:
            return self.PORT(option)
        if command == self.commands[9]:
            return self.PWD()
        if command == self.commands[10]:
            self.connection.sendall(b'Thank you for using my FTP server\n Good Bye <3')
            self.connection.close()
            sys.exit(0)
        if command == self.commands[11]:
            return self.RETR(option)
        if command == self.commands[12]:
            return self.USER(option)

    def CDUP(self):
        valid_cdup = False
        response = b'Changing to Parent Directory...\n'
        if os.path.isdir('..'):
            os.chdir('..')
            response = 'Directory Change Successful\n'
            valid_cdup = True
        else:
            response = 'ERROR: Directory does not exist.\n'

        self.record.log('CDUP Response: ' + response)
        return response, valid_cdup

    def CWD(self, options='.'):
        valid_cwd = False
        if os.path.isdir(options):
            os.chdir(options)
            response = 'CWD Success\n'
            valid_cwd = True
        else:
            response = 'ERROR: Directory does not exist.\n'

        self.record.log('CWD Response: ' + response)
        return response, valid_cwd

    def EPRT(self, args):
        response = None
        eprt_success = False

        delimiter = args[0]
        eprt_args = args[1:-1]
        list(filter(delimiter.__ne__, eprt_args))

        ip_type = eprt_args[0]
        if ip_type != 1 and ip_type != 2:
            response = 'Network Protocol not supported, use (1, 2)\n'

        ip = eprt_args[0]
        port = eprt_args[1]

        self.data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.data_socket.bind((ip, port))
        self.data_socket.listen(1)

        response = 'Data Socket opened on (' + str(ip) + ', ' + str(port) + ')\n'
        eprt_success = True

        self.record.log('EPRT Response: ' + response)
        return response, eprt_success

    def EPSV(self):
        pass

    def HELP(self):
        response = b'Supported Commands:\n'
        self.connection.sendall(response)

        commands = ''
        for command in self.commands:
            commands = commands + str(command) + ', '
        commands = commands[:-2] + '\n'

        self.record.log('HELP Response: OK\n')
        return commands, True

    def LIST(self, options='.'):
        valid_dir = False
        list_text = None
        response = ''
        self.connection.sendall(b'150 Directory Listing Sending...\n')
        if os.path.isdir(options):
            list_text = os.listdir(options)
            for _ in list_text:
                response = response + str(list_text.pop()) + '\n'
            valid_dir = True
        else:
            response = 'ERROR: Directory not found.\n'

        self.record.log('LIST Response: ' + response)
        return response, valid_dir

    def PASS(self, option):
        response = ''
        valid_pass = False

        with open(self.server.usersfile.rstrip(), 'r') as file:
            users = file.readlines()

        for user in users:
            if self.user_variable in user:
                password = user.split(':')[2]
                if option == password.rstrip():
                    valid_pass = True
                    self.password = password
                    self.attempts = 0
                    response = '230 Logged in.\n'
                else:
                    if self.attempts == 3:
                        response = 'Number of Login attempts used. Exiting...\n'
                        self.record.log('ERROR: ' + response)
                        sys.exit(1)
                    else:
                        response = 'Password incorrect. To try again enter PASS\n'
                        self.attempts += 1
                        self.record.log('BAD PASSWORD')

        self.record.log('PASS Response: ' + response)
        return response, valid_pass

    def PASV(self):
        self.pasvmode = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.server.host, 0))
        self.server_socket.listen(1)

        ip, port = self.server_socket.getsockname()

        self.record.log('Opened socket %s:%s', ip, port)
        response = '227 Entering Passive Mode (%s,%u,%u).\n' % \
                   (','.join(ip.split('.')), port >> 8 & 0xFF, port & 0xFF)

        return response, True

    def PORT(self, args):
        port_success = False

        server_info = args[-1].rstrip()
        server_info = server_info[1:-2].split(',')

        ip = server_info[0:-2]
        port = server_info[-2:]

        self.data_addr = str(ip[0] + '.' + ip[1] + '.' + ip[2] + '.' + ip[3])
        self.data_port = int(port[0]) * 256 + int(port[1])

        self.record.log('Custom addr and port %s:%s', self.data_addr, self.data_port)
        response = '200 Get port.\n'
        port_success = True

        return response, port_success

    def PWD(self):
        cwd = os.getcwd()
        return cwd, True

    def RETR(self, file):
        valid_retr = False
        data = None

        self.data_port, self.address = self.connection.accept()
        self.data_socket = FtpSocket(self.data_port, self.record)

        self.connection.sendall('150 Opening data connection.')
        if os.path.isfile(file):
            with open(file, 'r') as file:
                data = file.read(1024)

            while data:
                self.data_socket.send(data)
                data = file.read(1024)

            response = '226 Transfer complete.'
            valid_retr = True
        else:
            response = 'ERROR: No File matching given arg.'

        self.record.log('RETR Response: ' + response)
        return response, valid_retr

    def USER(self, option):
        response = ''
        valid_user = False

        with open(self.server.usersfile.rstrip(), 'r') as file:
            users = file.readlines()

        for user in users:
            if option in user:
                valid_user = True
                self.user_variable = option
                response = '331 Password required for ' + option + '\n'
        self.record.log('USER Response: ' + response)
        return response, valid_user


class FtpSocket:
    """
    The FtpSocket class handles socket related processes.
    it takes the port the server was started on for reference and
    the logger that is being used in this session to record activity.
    """
    BufferSize = 1024

    def __init__(self, port, logger):
        self.host = '127.0.0.1'
        self.port = port
        self.record = logger
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.bind((self.host, port))
        # (socket.gethostbyname(socket.getfqdn()))
        self.connection = None
        self.address = None
        self.record.log('Server IP: 127.0.0.1')
        self.record.log('Server Port: ' + str(self.port))
        self.serversocket.settimeout(60)

    def listen(self):
        try:
            self.record.log('Listening for connections...')
            self.serversocket.listen(5)
        except Exception as e:
            self.record.log('Error while listening for connections: ' + str(e))

    def accept(self):
        return self.serversocket.accept()

    def connect(self):
        response = None
        try:
            self.record.log('Attempting to connect to client...')
            self.serversocket.connect((self.host, self.port))
            response = self.serversocket.recv(1024)
            self.record.log('Connected to ' + str(self.address[0]) + ':' + str(self.address[1]))
            print('Connected to ' + str(self.address[0]) + ':' + str(self.address[1]) + ' successfully')
        except Exception as e:
            self.record.log('Error while connecting: ' + str(e))

        self.record.log('Server Response: ' + str(response))
        return response

    def send(self, message):
        totaldata = 0
        try:
            self.record.log('Attempting to send ' + message.rstrip())
            while totaldata < len(message):
                sentdata = self.serversocket.send(message[totaldata:])
                if sentdata is 0:
                    raise RuntimeError
                totaldata += sentdata
        except RuntimeError as e:
            self.record.log('Error trying to send data: ' + str(e))
        except Exception as e:
            self.record.log('Error: ' + str(e))

        self.record.log('Message "' + str(message.rstrip()) + '" sent successfully')

    def receive(self):
        dataframes = []
        totaldata = None
        try:
            data = self.serversocket.recv(1024)
            while data:
                dataframe = self.serversocket.recv(1024)
                if dataframe is '':
                    self.record.log('Error: Socket connection lost')
                    raise RuntimeError('Socket connection was broken')
                dataframes.append(dataframe.decode())
                totaldata += data
                data = self.serversocket.recv(1024)
            self.record.log('Data has been received from ' + self.address[1] + ':' + self.address[2])
            self.record.log('Total data received: ' + str(totaldata))
            return ''.join(dataframes)
        except Exception as e:
            self.record.log('Error: ' + str(e))

    def close(self):
        self.serversocket.close()

    # @staticmethod
    # def commands():
    #     commands = ['USER', 'PASS', 'CWD', 'QUIT', 'PASV', 'EPSV', 'PORT',
    #                 'EPRT', 'RETR', 'STOR', 'PWD', 'SYST', 'LIST', 'HELP']

    # def next_packet(self):
    #     received_packet = self.clientsocket.recv(16)
    #     print(received_packet)


class States:
    """
    Just a simple class with states defined for easy reference.
    """

    NULL_STATE = -1
    USER_REQUIRED = 0
    USER_ACCEPTED = 1
    USER_DECLINED = 2
    PASS_REQUIRED = 3
    PASS_ACCEPTED = 4
    PASS_DECLINED = 5
    CMD_SUCCESS = 6
    CMD_FAILURE = 7

    def __init__(self, status=None, message=None):
        if status is None:
            self.status = States.NULL_STATE
        else:
            self.status = status

        self.message = message

    @staticmethod
    def copy(state):
        newstate = deepcopy(state)
        newstate.status = state.status
        newstate.message = None

    @staticmethod
    def get_status(state):
        return state.status

    @staticmethod
    def get_message(state):
        return state.message


class StateMachine:

    """
    The StateMachine class works along with the States class for keeping track of the state
    and changing states through out the server threads.
    """

    def __init__(self, connection, address):
        self.connection = connection
        self.address = address

        self.states = []
        self.current = States.NULL_STATE
        self.states.append(self.current)

        if self.states is None:
            start = States.NULL_STATE
            self.states.append(start)

    def compute(self, response):
        compute = self.states.pop()
        if compute == States.NULL_STATE:
            if response.find('USER') == -1:
                return -1

    def update(self, command, command_boolean):
        current = self.states[0]
        if command == 'USER':
            if current == States.NULL_STATE:
                if command_boolean is True:
                    self.states.insert(0, States.USER_ACCEPTED)
                else:
                    self.states.insert(0, States.USER_DECLINED)
        elif command == 'PASS':
            if current == States.USER_ACCEPTED:
                if command_boolean is True:
                    self.states.insert(0, States.PASS_ACCEPTED)
                else:
                    self.states.insert(0, States.PASS_DECLINED)
        else:
            if current == States.PASS_ACCEPTED or current == States.CMD_SUCCESS:
                if command_boolean is True:
                    self.states.insert(0, States.CMD_SUCCESS)
                else:
                    self.states.insert(0, States.CMD_FAILURE)


class Logger:
    """
    Logger class that handles logging messages sent or received by the server
    and any important info pertaining to clients. General initialization, authentication,
    and errors will also be logged via this class.
    """

    def __init__(self, logfile):
        """
        Takes string from command line. Checks if file exists. If the file exists
        a number is inserted until the file doesnt exist.
        """
        count = 1
        original = logfile
        self.logger = None
        if logfile[-4:] != '.log' and logfile[-4:] != '.txt':
            original = logfile + '.log'
            logfile = logfile + '.log'
        while os.path.isfile(logfile):
            logfile = original[:-4] + str(count) + original[-4:]
            count = count + 1
        if original != logfile:
            print('Logfile name has been updated to', logfile)
        try:
            self.logger = open(logfile, 'a+')
        except PermissionError:
            print('Permission Error: Could not write to file')
            sys.exit(1)

    def log(self, info):
        try:
            if self.logger is None:
                raise TypeError
        except TypeError:
            print('Error creating log file')
        except Exception as e:
            print('Exception: ' + str(e))

        try:
            self.logger.write(str(datetime.now()) + ' ' + info + '\n')
        except Exception as e:
            print('Error: ' + str(e))


def main():

    """
    Where everything begins and the initialization of the server.
    """
    if len(sys.argv) != 3:
        print('Error: Required arguments not sufficient')
        sys.exit(1)

    record = Logger(sys.argv[1])
    record.log('Initialization of Logger.')

    if sys.argv[2].isdigit() and int(sys.argv[2]) in range(1, 65535):
        port = int(sys.argv[2])
    else:
        print('Error: Not a valid port')
        sys.exit(1)

    server = Server(port, record)
    try:
        server.ignition()
    finally:
        print('Saying Good Bye.')


if __name__ == '__main__':
    main()
