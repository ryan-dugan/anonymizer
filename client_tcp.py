import os.path
import socket
import sys


def validate_args():
    """
    Validate the command line arguments.

    Checks if the correct number of arguments are provided and if the port number is an integer.

    Returns:
    - tuple: A tuple containing the server IP address and port number
    """
    # check number of arguments
    if len(sys.argv) != 3:
        print 'Usage: client_tcp.py <server_IP> <port>'
        sys.exit(1)

    # check if port number is an integer
    try:
        port = int(sys.argv[2])
    except ValueError:
        print("Error: Port number must be an integer")
        sys.exit(1)

    return sys.argv[1], port


def send_file(clientSocket, filePath):

    """
    Sends a file over a TCP connection to the server.

    Parameters:
    - clientSocket (socket): The client TCP socket to communicate with the server.
    - filePath (str): The path to the file to be sent.

    Raises:
    - IOError: If there is an error opening or reading the file.
    """

    # open the file for reading, send data to server
    try:
        with open(filePath, 'rb') as fp:
            while 1:
                data = fp.read(1024)
                if not data:
                    break
                clientSocket.send(data)
    except IOError as e:
        print 'Error: Unable to open file', filePath, ':', e
        sys.exit(1)


def receive_file(clientSocket, filePath):

    """
    Receives a file from the server over a TCP connection and saves it to the specified file path.

    Parameters:
    - clientSocket (socket): The client TCP socket to communicate with the server.
    - filePath (str): The path where the received file will be saved.

    Raises:
    - IOError: If there is an error opening or writing to the file.
    """

    # get file name from file path
    fileName = os.path.basename(filePath)

    # receive data from server, create new copy of file
    try:
        with open(fileName, 'wb') as fp:
            while 1:
                data = clientSocket.recv(1024)
                fp.write(data)
                if len(data) < 1024:
                    break

    except IOError as e:
        print 'Error: Unable to open file ', fileName, ': ', e
        sys.exit(1)

    print 'File', fileName, 'downloaded.'


def main():

    """
    Main function to handle client operations for sending commands to a server over TCP.
    """

    # validate command line arguments
    serverIP, serverPort = validate_args()

    # create TCP socket for server
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # send request using clientSocket to establish TCP connection
    clientSocket.connect((serverIP, serverPort))

    # loop to get commands from user until user enters 'quit'
    while 1:

        # get user input for command
        userInput = raw_input('Enter Command: ')
        command = userInput.split(" ")

        # handle commands
        if command[0] == "put":

            # validate args
            if len(command) != 2:
                print 'Usage: put <file>'
                sys.exit(1)

            # get raw file path and file name
            filePath = r'' + command[1]
            fileName = os.path.basename(filePath)

            # send info to server, then call send_file()
            clientSocket.send('put')
            clientSocket.send(fileName.encode())
            clientSocket.send(b'\0')
            send_file(clientSocket, filePath)

            # get server response
            print 'Awaiting server response.'
            serverResponse = clientSocket.recv(1024)
            print 'Server response:', serverResponse

        elif command[0] == "get":

            # validate args
            if len(command) != 2:
                print 'Usage: get <file>'
                sys.exit(1)

            fileName = command[1]

            # send info to server, then call receive_file()
            clientSocket.send('get')
            clientSocket.send(fileName)
            receive_file(clientSocket, fileName)

        elif command[0] == "keyword":

            # validate args
            if len(command) != 3:
                print 'Usage: keyword <word> <file>'
                sys.exit(1)

            keyword = command[1]
            fileName = command[2]

            # send info to server
            clientSocket.send('keyword')
            clientSocket.send(keyword)
            clientSocket.send(b'\0')
            clientSocket.send(fileName)

            # get server response
            print 'Awaiting server response.'
            serverResponse = clientSocket.recv(1024)
            print 'Server response:', serverResponse.decode()

        elif command[0] == "quit":
            print 'Exiting program!'
            clientSocket.send('quit')
            clientSocket.close()
            sys.exit(1)
        else:
            print 'Invalid command: ', command[0]
            sys.exit(1)


if __name__ == '__main__':
    main()
