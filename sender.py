#Import Libraries needed for RDT
import sys
import socket
import datetime
import time
from checksum import checksum, checksum_verifier

#Used for the wait function
import logging
import threading
event = threading.Event()

CONNECTION_TIMEOUT = 60 # timeout when the sender cannot find the receiver within 60 seconds
FIRST_NAME = "Lenin"
LAST_NAME = "Perdomo"

#Encodes information into a packet of bytes
def make_pkt(seq_num, ack_num, data):

    #Check that the length of the data is not more than 20 bytes
    if len(bytes(data, 'utf-8')) > 20:
        return None

    #Make by calculating the data's checksum
    if data != '':
        packet_str = str(seq_num) + " " + str(ack_num) + " " + str(data) + " "
    else:
        packet_str = str(seq_num) + " " + str(ack_num) + '                      '
    checksum_str = checksum(packet_str)
    packet_str += checksum_str
    packet = bytes(packet_str, 'utf-8')

    #Return the packet
    return packet

#Returns True if the rcvpkt packet is corrupt
def corrupt(rcvpkt):
    if rcvpkt == None:
        return True

    #Return True if the packet is corrupt
    return not checksum_verifier(rcvpkt.decode('utf-8'))

#Checks if the ACK number of the recieved packet matches teh current ACK number of the sender
def isACK(rcvpkt, cur_ack):
    #Empty packet
    if rcvpkt == None:
        return False

    #Wrong length packet
    if len(rcvpkt) < 3:
        return False

    #Convert the recieved packet into a string
    rcvpkt_str = rcvpkt.decode('utf-8')

    #Invalid number at ACK position
    if not rcvpkt_str[2].isdigit():
        return False

    #Get the ACK number from the recieved packet
    rcv_ack = int(rcvpkt_str[2])

    #Check that ACK number matches the expected ACK number
    return rcv_ack == cur_ack

def start_sender(server_ip, server_port, connection_ID, loss_rate=0, corrupt_rate=0, max_delay=0, transmission_timeout=60, filename="declaration.txt"):
    """
     This function runs the sender, connnect to the server, and send a file to the receiver.
     The function will print the checksum, number of packet sent/recv/corrupt recv/timeout at the end. 
     The checksum is expected to be the same as the checksum that the receiver prints at the end.

     Input: 
        server_ip - IP of the server (String)
        server_port - Port to connect on the server (int)
        connection_ID - your sender and receiver should specify the same connection ID (String)
        loss_rate - the probabilities that a message will be lost (float - default is 0, the value should be between 0 to 1)
        corrupt_rate - the probabilities that a message will be corrupted (float - default is 0, the value should be between 0 to 1)
        max_delay - maximum delay for your packet at the server (int - default is 0, the value should be between 0 to 5)
        tranmission_timeout - waiting time until the sender resends the packet again (int - default is 60 seconds and cannot be 0)
        filename - the path + filename to send (String)

     Output: 
        checksum_val - the checksum value of the file sent (String that always has 5 digits)
        total_packet_sent - the total number of packet sent (int)
        total_packet_recv - the total number of packet received, including corrupted (int)
        total_corrupted_pkt_recv - the total number of corrupted packet receieved (int)
        total_timeout - the total number of timeout (int)

    """

    print("Student name: {} {}".format(FIRST_NAME, LAST_NAME))
    print("Start running sender: {}".format(datetime.datetime.now()))

    checksum_val = "00000"
    total_packet_sent = 0
    total_packet_recv = 0
    total_corrupted_pkt_recv = 0
    total_timeout =  0

    print("Connecting to server: {}, {}, {}".format(server_ip, server_port, connection_ID))

    #Contains all the 200 bytes of data sent
    data = ""

    #Open a socket connection
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        #Connect to the server
        s.connect((server_ip, server_port))

        #Send message to begin communication with the server
        server_message = 'HELLO S {} {} {} {}'.format(loss_rate, corrupt_rate, max_delay, connection_ID)
        s.sendall(bytes(server_message, 'utf-8'))

        #Handle server response messages
        while True:
            rcv_message = s.recv(1024).decode('utf-8')
            tokens = rcv_message.split()
            if 'OK' in tokens:
                break
            if 'WAITING' in tokens:
                continue
            else:
                print("Message received: " + rcv_message)
                quit()

        #Set the timer
        s.settimeout(float(sys.argv[-2]))

        #Get the filename from the command line arguments
        filename = sys.argv[-1]

        #Store the number of bytes that were sent without any errors
        bytes_sent_successfully = 0

        #Open the file and read the first 20 bytes of data from it
        with open(filename, 'r', encoding="utf8") as inputFile:

            #Keep count of number of iterations
            iter_num = 0

            #Continue to send 20 bytes of data from the file through each iteration, stop once the first 200 bytes have been sent
            while (bytes_sent_successfully < 200):

                #Read 20 bytes of data
                curData = inputFile.read(20)
                data += curData

                #Set the current ACK number of the sender
                cur_ack = 0

                #Set the timer
                s.settimeout(float(sys.argv[-2]))

                try:

                    #Wait for call 0 from above - rdt_send(data)
                    sndpkt = make_pkt(0, cur_ack, curData)
                    s.sendall(sndpkt)

                    #Increment the packet sent counter
                    total_packet_sent += 1

                    #Wait for call 0 from above - rdt_rcv(rcvpkt)
                    rcvpkt = s.recv(30)

                    #Stop receiving data once the connection closes
                    if not rcvpkt:
                        break

                    #Wait for ACK0 - rdt_rcv(rcvpkt) && (corrupt(rcvpkt) || isACK(rcvpkt,1))
                    if (rcvpkt != None):
                        while (corrupt(rcvpkt) or not isACK(rcvpkt, cur_ack)):

                            #Increment the number of packets received
                            total_packet_recv += 1
                            total_corrupted_pkt_recv += 1

                            #try to receive the packet again
                            rcvpkt = s.recv(30)

                            #Stop receiving data once the connection closes
                            if not rcvpkt:
                                break

                            #Move to the next in the FSM if correct packet is received
                            if (not corrupt(rcvpkt) and isACK(rcvpkt, cur_ack)):
                                break


                    #Wait for ACK0 ==> Wait for call 1 from above - rdt_rcv(rcvpkt) && notcorrupt(rcvpkt) && isACK(rcvpkt, 0)
                    if (rcvpkt != None):
                        if (not corrupt(rcvpkt) and isACK(rcvpkt, cur_ack)):
                            total_packet_recv += 1

                            #Break out from the loop and move to the next state in the FSM
                            bytes_sent_successfully += 20

                #Wait for ACK0 - timeout
                except socket.timeout:

                    #This loop keeps running as long as proper packet has not been received
                    while True:

                        #Set the timer
                        s.settimeout(float(sys.argv[-2]))

                        try:
                            #Increment the timeout counter
                            total_timeout += 1

                            #Resend packet
                            s.sendall(sndpkt)

                            #Increment the packet received count
                            total_packet_sent += 1

                            #Try to receive the packet again
                            rcvpkt = s.recv(30)

                            #Stop receiving data once the connection closes
                            if not rcvpkt:
                                break

                            #Wait for ACK0 - rdt_rcv(rcvpkt) && (corrupt(rcvpkt) || isACK(rcvpkt,1))
                            if (rcvpkt != None):
                                while (corrupt(rcvpkt) or not isACK(rcvpkt, cur_ack)):  

                                    #Increment the packet received counters
                                    total_packet_recv += 1
                                    total_corrupted_pkt_recv += 1

                                    #Try to receive the packet again
                                    rcvpkt = s.recv(30)

                                    #Stop the program once the connection closes
                                    if not rcvpkt:
                                        break

                                    #Move to the next once a correct packet is received
                                    if (not corrupt(rcvpkt) and isACK(rcvpkt, cur_ack)):
                                        break


                            #Wait for ACK0 ==> Wait for call 1 from above - rdt_rcv(rcvpkt) && notcorrupt(rcvpkt) && isACK(rcvpkt, 0)
                            if (rcvpkt != None):
                                if (not corrupt(rcvpkt) and isACK(rcvpkt, cur_ack)):
                                    total_packet_recv += 1

                                    #Break out from the loop and move to the next state in the FSM
                                    bytes_sent_successfully += 20
                                    break

                        #Wait for ACK0 - timeout
                        except socket.timeout:

                            #Start the loop over again (timer reset at the begenning of the loop)
                            continue

                #Update the current ACK number
                cur_ack = 1

                #Update curData to send the next 20 bytes of data
                curData = inputFile.read(20)     
                data += curData

                #Set the timer
                s.settimeout(float(sys.argv[-2]))

                try:

                    #Wait for call 1 from above ==> Wait for ACK1 - rdt_send(data)
                    sndpkt = make_pkt(1, cur_ack, curData)
                    s.sendall(sndpkt)
                    total_packet_sent += 1

                    #Wait for call 1 from above - rdt_rcv(rcvpkt)
                    rcvpkt = s.recv(30)

                    #Wait for ACK1 rdt_rcv(rcvpkt) && (corrupt(rcvpkt) || isACK(rcvpkt,1))
                    if (rcvpkt != None):
                        while (corrupt(rcvpkt) or not isACK(rcvpkt, cur_ack)):

                            #Increment the received packet count
                            total_packet_recv += 1
                            total_corrupted_pkt_recv += 1

                            #Try to receive the packet again
                            rcvpkt = s.recv(30)

                            #Stop receiving data once the connection closes
                            if not rcvpkt:
                                break

                            #Move to the next state once a correct packet is received
                            if (not corrupt(rcvpkt) and isACK(rcvpkt, cur_ack)):
                                break


                    #Wait for ACK1 ==> Wait for call 0 from above - rdt_rcv(rcvpkt) && notcorrupt(rcvpkt) && isACK(rcvpkt, 0)
                    if (rcvpkt != None):
                        if (not corrupt(rcvpkt) and isACK(rcvpkt, cur_ack)):

                            #Increment the number of bytes sent and packets received successfully
                            total_packet_recv += 1
                            bytes_sent_successfully += 20

                #Wait for ACK1 - timeout
                except socket.timeout:

                    #This loop keeps running as long as proper packet has not been received
                    while True:

                        #Set the timer
                        s.settimeout(float(sys.argv[-2]))

                        #Increment the timeout counter
                        total_timeout += 1

                        try:
                            #Resend the packet through UDT
                            #rdt_send(1, cur_ack, curData, s)
                            s.sendall(sndpkt)

                            #Increment the number of packets sent
                            total_packet_sent += 1

                            #Try to receive the packet again
                            rcvpkt = s.recv(30)

                            #Wait for ACK1 rdt_rcv(rcvpkt) && (corrupt(rcvpkt) || isACK(rcvpkt,1))
                            if (rcvpkt != None):
                                while (corrupt(rcvpkt) or not isACK(rcvpkt, cur_ack)):

                                    #Increment the count of packages received
                                    total_packet_recv += 1
                                    total_corrupted_pkt_recv += 1

                                    #Try to receive the packet again
                                    rcvpkt = s.recv(30)

                                    #Stop if the socket closes
                                    if not rcvpkt:
                                        break

                                    #Move to the next state a correct packet is received
                                    if (not corrupt(rcvpkt) and isACK(rcvpkt, cur_ack)):
                                        break


                            #Wait for ACK1 ==> Wait for call 0 from above - rdt_rcv(rcvpkt) && notcorrupt(rcvpkt) && isACK(rcvpkt, 0)
                            if (rcvpkt != None):
                                if (not corrupt(rcvpkt) and isACK(rcvpkt, cur_ack)):

                                    #Increment the number of packets received, bytes sent, and break
                                    total_packet_recv += 1
                                    bytes_sent_successfully += 20
                                    break

                        #Wait for ACK1 - timeout
                        except socket.timeout:

                            continue

                #Increment the iteration number
                iter_num += 1

                #Stop the program once five iterations have been completed (Possible TODO: Find a better way to do this)
                if iter_num == 5:
                    break

            #Update the checksum_val
            checksum_val = checksum(data)


    print("Finish running sender: {}".format(datetime.datetime.now()))

    # PRINT STATISTICS
    print("File checksum: {}".format(checksum_val))
    print("Total packet sent: {}".format(total_packet_sent))
    print("Total packet recv: {}".format(total_packet_recv))
    print("Total corrupted packet recv: {}".format(total_corrupted_pkt_recv))
    print("Total timeout: {}".format(total_timeout))

    return (checksum_val, total_packet_sent, total_packet_recv, total_corrupted_pkt_recv, total_timeout)
 
if __name__ == '__main__':
    # CHECK INPUT ARGUMENTS
    if len(sys.argv) != 9:
        print("Expected \"python3 PA2_sender.py <server_ip> <server_port> <connection_id> <loss_rate> <corrupt_rate> <max_delay> <transmission_timeout> <filename>\"")
        exit()

    # ASSIGN ARGUMENTS TO VARIABLES
    server_ip, server_port, connection_ID, loss_rate, corrupt_rate, max_delay, transmission_timeout, filename = sys.argv[1:]
    
    # RUN SENDER
    start_sender(server_ip, int(server_port), connection_ID, loss_rate, corrupt_rate, max_delay, float(transmission_timeout), filename)
