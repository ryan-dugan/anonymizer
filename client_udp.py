import os
import socket
import sys


def validate_args():
    """
    Validate the command line arguments.

    Checks if the correct number of arguments are provided and if the port number is an integer.

    Returns:
        tuple: A tuple containing the server IP address and port number
    """
    # check number of arguments
    if len(sys.argv) != 3:
        print 'Usage: client_udp.py <server_IP> <port>'
        sys.exit(1)

    # check if port number is an integer
    try:
        port = int(sys.argv[2])
    except ValueError:
        print("Error: Port number must be an integer")
        sys.exit(1)

    return sys.argv[1], port


def send_file(clientSocket, serverIP, serverPort, filePath):

    """
    Send a file over a UDP connection to a specified server.

    Implements "stop-and-wait" functionality, i.e. after each chunk is sent, client waits for an ACK from the server.

    Parameters:
    - clientSocket (socket.socket): The client UDP socket to communicate with the server.
    - serverIP (str): The address of the server.
    - serverPort (int): The port number of the server.
    - filePath (str): The path of the file to be sent.

    Raises:
    - IOError: If the file specified by filePath can't be opened.
    - socket.timeout: If an ACK message is not received within 1 second after sending a chunk.
    """
    # try to open the file for reading
    try:
        with open(filePath, 'rb') as fp:
            data = fp.read()
    except IOError as e:
        print 'Error: Unable to open file', filePath, ':', e
        sys.exit(1)

    # first send LEN message
    encoded_data = data.encode()
    num_bytes = len(encoded_data)
    len_msg = 'LEN:' + str(num_bytes)
    clientSocket.sendto(len_msg, (serverIP, serverPort))
    if num_bytes == 0:
        print 'Length of data cannot be 0.'
        sys.exit(1)

    # define chunk size
    chunk_size = 1000

    # calculate number of chunks to be sent
    num_chunks = (num_bytes + chunk_size - 1) // chunk_size

    # split data into equal chunks of 1000 bytes each
    data_chunks = [encoded_data[i * chunk_size:(i + 1) * chunk_size] for i in range(num_chunks)]

    # set timeout to 1 second
    clientSocket.settimeout(1)

    # send one chunk at a time, stop and wait for ACK message after each transmission
    for i in range(num_chunks):

        clientSocket.sendto(data_chunks[i], (serverIP, serverPort))
        try:
            ack_msg, serverAddress = clientSocket.recvfrom(1024)
        except socket.timeout:
            print 'Did not receive ACK. Terminating.'
            sys.exit(1)

    # receive FIN message, terminate connection
    fin_msg, serverAddress = clientSocket.recvfrom(1024)
    if fin_msg == 'FIN':

        # get server response
        print 'Awaiting server response.'
        serverResponse, serverIP = clientSocket.recvfrom(1024)
        print 'Server response:', serverResponse

        clientSocket.close()
    else:
        print 'Error: Expected FIN message, received:', fin_msg


def receive_file(clientSocket, serverIP, filePath):

    """
    Receive a file over a UDP connection from a specified server.

    Implements "stop-and-wait" functionality, i.e. after each chunk is received,
    sends ACK to server before receiving next chunk.

    Parameters:
    - clientSocket (socket.socket): The client UDP socket to communicate with the server.
    - serverIP (str): The address of the server.
    - filePath (str): The path where the received file will be saved.

    Raises:
    - Error: If the length message does not start with 'LEN:'.
    - ValueError: If the substring after 'LEN:' cannot be converted to an integer.
    - IOError: If there is an error while writing the received file to the disk.
    - socket.timeout: If no data is received within 1 second after sending LEN message,
        or if no data is received within 1 second after issuing an ACK.
    """

    # get file name from file path
    fileName = os.path.basename(filePath)

    # first get length of data to be transferred
    len_msg, serverIP = clientSocket.recvfrom(1024)

    # check length message for string "LEN:Bytes"
    if len_msg.startswith('LEN:'):
        str_bytes = len_msg[4:]
        try:
            # convert substring to int
            num_bytes = int(str_bytes)
            if num_bytes == 0:
                print 'Length of data cannot be 0.'
                sys.exit(1)
        except ValueError:
            # if substring is not a valid integer
            print "Invalid number of bytes:", str_bytes
            sys.exit(1)
    else:
        print 'Error: Expected LEN message \'LEN:Bytes\', received', len
        sys.exit(1)

    data_chunks = []
    ack_msg = 'ACK'

    # calculate the number of chunks expected
    chunk_size = 1000
    num_chunks = (num_bytes + chunk_size - 1) // chunk_size

    # handle LEN timeout
    clientSocket.settimeout(1)
    try:
        # receive first chunk of data
        data_chunk, serverIP = clientSocket.recvfrom(1000)
        data_chunks.append(data_chunk)
    except socket.timeout:
        print 'Did not receive data. Terminating.'
        sys.exit(1)

    # ACK first chunk
    clientSocket.sendto(ack_msg, serverIP)

    # start receiving chunks, send ACK message after each chunk
    for i in range(1, num_chunks):

        # handle timeout after each data packet
        try:
            data_chunk, serverIP = clientSocket.recvfrom(1000)
            data_chunks.append(data_chunk)
        except socket.timeout:
            print 'Data transmission terminated prematurely.'
            sys.exit(1)

        # send ACK message
        clientSocket.sendto(ack_msg, serverIP)

    # send FIN message once all data has been received
    fin_msg = 'FIN'
    clientSocket.sendto(fin_msg, serverIP)

    # write each chunk to new file
    try:
        with open(fileName, 'wb') as fp:
            for chunk in data_chunks:
                fp.write(chunk)
    except IOError as e:
        print 'Error: Unable to open file ', fileName, ': ', e
        sys.exit(1)

    print 'File', fileName, 'downloaded.'


def main():

    """
    Main function to handle client operations for sending commands to a server over UDP.
    """

    # validate command line arguments
    serverIP, serverPort = validate_args()

    while 1:

        # create socket
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # get user input for command
        userInput = raw_input('Enter Command: ')
        command = userInput.split(" ")

        # check if the command is valid
        if command[0] == "put":

            # validate args
            if len(command) != 2:
                print 'Usage: put <file>'
                sys.exit(1)

            # get raw file path and file name
            filePath = r'' + command[1]
            fileName = os.path.basename(filePath)

            if not os.path.isfile(filePath):
                print 'File', filePath, 'does not exist.'
                sys.exit(1)

            # send info to server, then call send_file
            clientSocket.sendto('put', (serverIP, serverPort))
            clientSocket.sendto(fileName.encode(), (serverIP, serverPort))
            send_file(clientSocket, serverIP, serverPort, filePath)

        elif command[0] == "get":

            # validate args
            if len(command) != 2:
                print 'Usage: get <file>'
                sys.exit(1)

            filePath = command[1]

            # send command and corresponding arguments to the server
            clientSocket.sendto('get', (serverIP, serverPort))
            clientSocket.sendto(filePath, (serverIP, serverPort))

            # check to make sure file exists at the server
            server_file_exists, (serverIP, serverPort) = clientSocket.recvfrom(1024)
            print 'server file exists:', server_file_exists
            if server_file_exists == 'True':
                receive_file(clientSocket, serverIP, filePath)
            else:
                print 'Server could not find file', filePath
                sys.exit(1)

        elif command[0] == "keyword":

            # validate args
            if len(command) != 3:
                print 'Usage: keyword <word> <file>'
                sys.exit(1)

            keyword = command[1]
            filePath = command[2]

            # send command and corresponding arguments to the server
            clientSocket.sendto('keyword', (serverIP, serverPort))
            clientSocket.sendto(keyword, (serverIP, serverPort))
            clientSocket.sendto(filePath, (serverIP, serverPort))

            print 'Awaiting server response.'
            serverResponse, (serverIP, serverPort) = clientSocket.recvfrom(1024)
            print 'Server response:', serverResponse

        elif command[0] == "quit":

            # exit the program and send quit command to server so the server will also exit
            print 'Exiting program!'
            clientSocket.sendto('quit', (serverIP, serverPort))
            clientSocket.close()
            sys.exit(1)

        # handle unknown commands
        else:
            print 'Invalid command: ', command[0]
            sys.exit(1)


if __name__ == '__main__':
    main()