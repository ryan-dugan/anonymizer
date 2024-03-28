
# The Anonymizer: Socket Programming and Reliable Data Transfer

The Anonymizer is a basic client-server application that anonymizes user-specified words from a text file. The real purpose of this project is to practice my socket programming / transport layer skills by implementing two reliable data transfer protocols.

The project comes in two versions: one that implements stock TCP for reliable data transfer, and one that implements "stop-and-wait" reliability at the application layer using UDP for transport.

## The Application

**Anonymization functionality:** The application allows a user to upload a text file of arbitrary size along with a keyword to be anonymized. The file will then be loaded, read and anonymized at the server and the redacted text will be stored in a new file. The anonymization function will replace the keyword with the equal amount of the symbol X.

>For example, if the target keyword is “networking” all instances of that word in a file
will be replaced with “XXXXXXXXXX”.

Once the server is done anonymizing, it will issue a message to the user indicating the output filename. The server will then allow the client to download the output file.

**Supported Commands:**
- **put <file\>** : Copy a file from the client to the server, which takes as an input argument the full path to a file *<file\>* on the client.

>**Example execution:**
>
>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;put test.txt
>
>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;or
>
>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;put C:\Python27\test.txt
>

- **get <file\>** : Copy a file from a server to a client (get), which also takes as an argument the full
path to a file *<file\>* on the server. 

>**Example execution:**
>
>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;get test.txt
>
>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;or
>
>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;get C:\Python27\test.txt
>

- **keyword <word\> <file\>** : Allow the user to specify a keyword to be anonymized and a target file, in which to anonymize.
>**Example execution:**
>
>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;keyword github test.txt
>

- **quit** : Quit the program per user request.

## Transport Layer Functionality

**TCP** (Transmission Control Protocol) is a connection-oriented protocol that offers reliability at the transport layer. TCP uses a three-way handshake to check for data transmission errors, retransmits data that is not delivered after a timeout period, and offers network congestion control.

**UDP** (User Datagram Protocol) is a message-oriented protocol that prioritizes speed and efficiency over data reliability. UDP is a "best effort delivery" protocol, mainly used for bandwidth-intensive applications that can tolerate data loss. It can send a large number of packets at a time with fewer delays in transmission, at the risk of losing data or sending data out of order.

For the TCP version of this application, the implementation is very straightforward - this is because TCP is doing most of the work for us under the hood.

For the UDP version however, we have to implement our own reliable data transfer at the application layer.

We do this using "stop-and-wait" reliability - implementing a series of checks on top of UDP that ensures that data is successfully transmitted between the client and server.

- Sender calculates the amount of data to be transmitted and sends a "length" message (LEN) to the receiver, letting them know how many bytes of data to expect.
- Sender splits data into equal 1000 byte chunks, and sends the data one chunk at a time.
- After each chunk is transmitted, the sender waits for an acknowledgement (ACK) from the receiver.
- Once the receiver has received all bytes of data (specified in the LEN message), the receiver sends a message (FIN) indicating that the file has finished uploading.

- Timeouts:
	- If no data arrives at the receiver within one second of the reception of a LEN message, the receiver terminates, displaying:
	>*Did not receive data. Terminating.*
	- If no ACK is received by the sender within one second of transmitting a data packet, the sender terminates, displaying:
	>*Did not receive ACK. Terminating.*
	- If no data arrives at the receiver within one second of issuing an ACK, the receiver terminates, displaying:
	>*Data transmission  terminated prematurely.*

<h2>Languages and Utilities Used</h2>

- <b>Python:</b> The programming language used for coding this project.

<h2>Environments Used </h2>

- <b>PyCharm:</b> The integrated development environment (IDE) utilized for development.
- <b>Python 2.7.16:</b> The python version used for coding this project.

<h2>Program walk-through:</h2>

Note that the user interface is identical between the TCP and UDP versions.

To start the server, you must specify the port number as a command line argument. For example, for port number 8080:
>C:\Users\yourName\yourDirectory> python server_udp.py 8080

To start the client, you must specify the server IP address followed by the server port number as command line arguments. For example, for server IP 127.0.0.1 and server port number 8080:
>C:\Users\yourName\yourDirectory> python client_udp.py 127.0.0.1 8080

Also note that the server must be running before trying to start the client.

<p align="center">
Client Execution: <br/>
<img src="https://i.imgur.com/rT9lGxG.png" height="80%" width="80%" alt="Client terminal"/>
<br />
<br />
Server Output:  <br/>
<img src="https://i.imgur.com/4ZfIfUu.png" height="80%" width="80%" alt="Server terminal"/>
<br />
<br />
Test file before anonymizing: <br/>
<img src="https://i.imgur.com/5FZzafp.png" height="50%" width="50%" alt="test1.txt"/>
<br />
<br />
Test file after anonymizing: <br/>
<img src="https://i.imgur.com/69yQPmA.png" height="50%" width="50%" alt="test1_anon.txt"/>
<br />
<br />
