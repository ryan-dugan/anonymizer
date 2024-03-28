import os
import socket
import sys


def validate_args():
    """
    Validate the command line arguments.

    Checks if the correct number of arguments are provided and if the port number is an integer.

    Returns:
    - tuple: A tuple containing the server IP address and port number
    """
    # Check number of arguments
    if len(sys.argv) != 2:
        print 'Usage: server_tcp.py <port>'
        sys.exit(1)

    # Check if port number is an integer
    try:
        port = int(sys.argv[1])
    except ValueError:
        print("Error: Port number must be an integer")
        sys.exit(1)

    return port


def receive_file(connectionSocket, fileName):

    """
    Receives a file from the client over a TCP connection and saves it to the specified file.

    Parameters:
    - connectionSocket (socket.socket): The server TCP socket connected to the client.
    - fileName (str): The name of the file to save the received data.

    Raises:
    - IOError: If there is an error opening or writing to the file.
    """

    # read each line in a loop, create new copy of file
    try:
        with open(fileName, 'wb') as fp:
            while 1:
                data = connectionSocket.recv(1024)
                fp.write(data)
                if len(data) < 1024:
                    break
    except IOError as e:
        print 'Error: Unable to open file ', fileName, ': ', e
        sys.exit(1)

    connectionSocket.send('File uploaded.')

    print 'Done receiving file.'


def send_file(connectionSocket, fileName):

    """
    Sends a file over a TCP connection to the client.

    Parameters:
    - connectionSocket (socket.socket): The server TCP socket connected to the client.
    - fileName (str): The name of the file to be sent.

    Raises:
    - IOError: If there is an error opening the file.
    """

    # open the file for reading, send data to client
    try:
        with open(fileName, 'rb') as fp:
            while 1:
                data = fp.read(1024)
                if not data:
                    connectionSocket.send('\0')
                    break
                connectionSocket.send(data)
    except IOError as e:
        print 'Error: Unable to open file ', fileName, ': ', e
        sys.exit(1)

    print 'Done sending file.'


def anon(connectionSocket, keyword, fileName):

    """
    Anonymizes a text file by replacing occurrences of a given keyword with 'X's,
    and sends the anonymized file name to the client.

    Parameters:
        connectionSocket (socket.socket): The socket connected to the client.
        keyword (str): The keyword to be anonymized.
        fileName (str): The name of the file to be anonymized.

    Raises:
        IOError: If there is an error opening the file.
    """

    # open the file for reading, and anonymize the keyword
    try:
        with open(fileName, 'rb') as og_fp:
            og_text = og_fp.read()
            anon_text = og_text.replace(keyword.encode(), b'X' * len(keyword))
    except IOError as e:
        print 'Error: Unable to open file ', fileName, ': ', e
        sys.exit(1)

    # get anonymized file name
    raw_file_name = fileName[:-4]
    anon_file_name = raw_file_name + '_anon.txt'

    # create the anonymized file and write the content
    try:
        with open(anon_file_name, 'wb') as anon_fp:
            anon_fp.write(anon_text)
    except IOError as e:
        print 'Error: Unable to open file ', anon_file_name, ': ', e
        sys.exit(1)

    # send the server response to the client
    serverResponse = 'File ' + fileName + ' anonymized. Output file is ' + anon_file_name
    connectionSocket.send(serverResponse.encode())

    print 'Done anonymizing file.'


def main():

    """
    Main function to handle server operations for receiving commands from a client over TCP.
    """

    # create socket, wait for incoming connection request from client
    serverPort = validate_args()
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(('', serverPort))

    # server begins listening for incoming TCP requests
    serverSocket.listen(1)

    # server waits on accept() for incoming request, new socket created on return
    connectionSocket, addr = serverSocket.accept()

    while 1:
        # read bytes from socket (but not address like UDP)
        command = connectionSocket.recv(1024)

        # command handling
        if command == 'put':

            fileNameRaw = b''
            while 1:
                data = connectionSocket.recv(1)
                if data == b'\0':  # check for null byte delimiter
                    break
                fileNameRaw += data

            fileName = fileNameRaw.decode()

            # receive_file(connectionSocket, fileName)
            # read each line in a loop, create new copy of file
            receive_file(connectionSocket, fileName)

        elif command == 'get':

            fileName = connectionSocket.recv(1024)
            send_file(connectionSocket, fileName)

        elif command == 'keyword':

            keywordRaw = b''
            while 1:
                data = connectionSocket.recv(1)
                if data == b'\0':  # check for null byte delimiter
                    break
                keywordRaw += data

            keyword = keywordRaw.decode()
            fileName = connectionSocket.recv(1024)  # this could be file path, have to handle to get file name

            anon(connectionSocket, keyword, fileName)

        elif command == 'quit':
            print 'Exiting program!'
            sys.exit(1)


if __name__ == '__main__':
    main()
