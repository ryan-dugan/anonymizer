import socket
import os
import sys


def validate_args():
    """
    Validate the command line arguments.

    Checks if the correct number of arguments are provided and if the port number is an integer.

    Returns:
        tuple: A tuple containing the server IP address and port number
    """
    # check number of arguments
    if len(sys.argv) != 2:
        print 'Usage: server_tcp.py <port>'
        sys.exit(1)

    # check if port number is an integer
    try:
        port = int(sys.argv[1])
    except ValueError:
        print("Error: Port number must be an integer")
        sys.exit(1)

    return port


def receive_file(serverSocket, fileName):

    """
    Receive a file from a client over UDP and save it locally.

    Implements "stop-and-wait" functionality, i.e. after each chunk is received,
    sends ACK to client before receiving next chunk.

    Parameters:
    - serverSocket (socket): The server UDP socket for communicating with the client.
    - fileName (str): The name of the file to be saved.

    Raises:
    - Error: If the length message does not start with 'LEN:'.
    - ValueError: If the substring after 'LEN:' cannot be converted to an integer.
    - IOError: If there is an error while writing the received file to the disk.
    - socket.timeout: If no data is received within 1 second after sending LEN message,
        or if no data is received within 1 second after issuing an ACK.
    """

    # first get length of data to be transferred
    len_msg, clientAddress = serverSocket.recvfrom(1024)

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
        print 'Error: Expected LEN message \'LEN:Bytes\', received', len_msg
        sys.exit(1)

    data_chunks = []
    ack_msg = 'ACK'

    # calculate the number of chunks expected
    chunk_size = 1000
    num_chunks = (num_bytes + chunk_size - 1) // chunk_size

    # handle LEN timeout
    serverSocket.settimeout(1)
    try:
        # receive first chunk of data
        data_chunk, clientAddress = serverSocket.recvfrom(1000)
        data_chunks.append(data_chunk)
    except socket.timeout:
        print 'Did not receive data. Terminating.'
        sys.exit(1)

    # ACK first chunk
    serverSocket.sendto(ack_msg, clientAddress)

    # start receiving chunks, send ACK message after each chunk
    for i in range(1, num_chunks):

        # handle timeout after each data packet
        try:
            data_chunk, clientAddress = serverSocket.recvfrom(1000)
            data_chunks.append(data_chunk)
        except socket.timeout:
            print 'Data transmission terminated prematurely.'
            sys.exit(1)

        # send ACK message
        serverSocket.sendto(ack_msg, clientAddress)

    # send FIN message once all data has been received
    fin_msg = 'FIN'
    serverSocket.sendto(fin_msg, clientAddress)

    # send response to client
    serverResponse = 'File uploaded.'
    serverSocket.sendto(serverResponse, clientAddress)

    # write each chunk to new file
    try:
        with open(fileName, 'wb') as fp:
            for chunk in data_chunks:
                fp.write(chunk)
    except IOError as e:
        print 'Error: Unable to open file ', fileName, ': ', e
        sys.exit(1)

    print 'Done receiving file.'


def send_file(serverSocket, clientAddress, filePath):

    """
    Sends a file over a UDP connection to the client.

    Implements "stop-and-wait" functionality, i.e. after each chunk is sent, server waits for an ACK from the client.

    Parameters:
    - serverSocket (socket.socket): The server UDP socket to communicate with the client.
    - clientAddress (str): The address of the client.
    - filePath (str): The path of the file to be sent.

    Raises:
    - IOError: If the file specified by filePath can't be opened.
    - socket.timeout: If an ACK message is not received within 1 second after sending a chunk.
    """

    # read in data from file
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
    serverSocket.sendto(len_msg, clientAddress)
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
    serverSocket.settimeout(1)

    for i in range(num_chunks):

        # send one chunk at a time, stop and wait for ACK message after each transmission
        serverSocket.sendto(data_chunks[i], clientAddress)
        try:
            ack_msg, clientAddress = serverSocket.recvfrom(1024)
        except socket.timeout:
            print 'Did not receive ACK. Terminating.'
            sys.exit(1)

    # receive FIN message, terminate connection
    fin_msg, clientAddress = serverSocket.recvfrom(1024)
    if fin_msg == 'FIN':
        serverSocket.close()
    else:
        print 'Error: Expected FIN message, received:', fin_msg

    print 'Done sending file.'


def anon(serverSocket, clientAddress, keyword, filePath):

    """
    Anonymizes a text file by replacing occurrences of a given keyword with 'X's,
    and sends the anonymized file name to the client.

    Parameters:
    - serverSocket (socket.socket): The server UDP socket to communicate with the client.
    - clientAddress (tuple): The address of the client.
    - keyword (str): The keyword to be anonymized.
    - filePath (str): The path to the file to be anonymized.

    Raises:
    - IOError: If there is an error opening or reading the file.
    - IOError: If there is an error creating or writing to the anonymized file.
    """

    # get file name from file path
    fileName = os.path.basename(filePath)

    # open the file for reading, anonymize text
    try:
        with open(filePath, 'rb') as og_fp:
            og_text = og_fp.read()
            anon_text = og_text.replace(keyword.encode(), b'X' * len(keyword))
    except IOError as e:
        print 'Error: Unable to open file ', filePath, ': ', e
        sys.exit(1)

    # get anonymized file name
    raw_file_name = fileName[:-4]
    anon_file_name = raw_file_name + '_anon.txt'

    # create new anonymized file
    try:
        with open(anon_file_name, 'wb') as anon_fp:
            anon_fp.write(anon_text)
    except IOError as e:
        print 'Error: Unable to open file ', anon_file_name, ': ', e
        sys.exit(1)

    # send server response
    serverResponse = 'File ' + fileName + ' anonymized. Output file is ' + anon_file_name
    serverSocket.sendto(serverResponse, clientAddress)

    print 'Done anonymizing file.'


def main():

    """
    Main function to handle server operations for receiving commands from a client over UDP.
    """

    # validate command line arguments
    serverPort = validate_args()

    while 1:

        # create socket, reset the timeout
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serverSocket.bind(('', serverPort))
        serverSocket.settimeout(None)

        # get command from client
        command, clientAddress = serverSocket.recvfrom(1024)

        # command handling
        if command == 'put':

            fileName, clientAddress = serverSocket.recvfrom(1024)
            receive_file(serverSocket, fileName)

        elif command == 'get':

            filePath, clientAddress = serverSocket.recvfrom(1024)

            # send a message to the client indicating the file exists
            fileExists = False
            if os.path.isfile(filePath):
                fileExists = True
            serverSocket.sendto(str(fileExists), clientAddress)

            send_file(serverSocket, clientAddress, filePath)

        elif command == 'keyword':

            keyword, clientAddress = serverSocket.recvfrom(1024)
            filePath, clientAddress = serverSocket.recvfrom(1024)
            anon(serverSocket, clientAddress, keyword, filePath)

        elif command == 'quit':
            print 'Exiting program!'
            sys.exit(1)


if __name__ == '__main__':
    main()