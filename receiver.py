#Import Libraries needed to Implement RDT
import sys
import time
import socket
import datetime 
import time
from checksum import checksum, checksum_verifier

CONNECTION_TIMEOUT = 60 # timeout when the receiver cannot find the sender within 60 seconds
FIRST_NAME = "Lenin"
LAST_NAME = "Perdomo"

#Encodes information into a packet of bytes
def make_pkt(seq_num, ack_num, rcvpkt):

    #Convert the packet into a string
    rcvpkt_str = rcvpkt.decode('utf-8')

    #First 25 bytes of data (5 checksum bytes not included yet)
    packet_str = "  " + str(ack_num) + "                      "
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

#Checks if the sequence number of the packet received matches the current sequence number of the receiver
def has_seq(rcvpkt, cur_seq):
    if rcvpkt == None:
        return False

    #Wrong length packet
    if len(rcvpkt) < 1:
        return False

    #Convert the received packet into a string
    rcvpkt_str = rcvpkt.decode('utf-8')

    #Invalid number at sequence number position
    if not rcvpkt_str[0].isdigit():
        return False
    
    #Get the sequence number from the received packet
    rcv_seq = int(rcvpkt_str[0])

    #Check that the sequence number matches the expected sequence number
    return rcv_seq == cur_seq

#Extracts the data from the received packet
def extract(rcvpkt):
    #Get the contents from the packet
    pkt_str = rcvpkt.decode('utf-8')
    
    #Extract the 20 bytes of data string from the 30 bytes packet
    data = pkt_str[4:-6]

    #Remove the extra whitespace at the end of data and return it
    return data

def start_receiver(server_ip, server_port, connection_ID, loss_rate=0.0, corrupt_rate=0.0, max_delay=0.0):
    """
     This function runs the receiver, connnect to the server, and receiver file from the sender.
     The function will print the checksum of the received file at the end. 
     The checksum is expected to be the same as the checksum that the sender prints at the end.

     Input: 
        server_ip - IP of the server (String)
        server_port - Port to connect on the server (int)
        connection_ID - your sender and receiver should specify the same connection ID (String)
        loss_rate - the probabilities that a message will be lost (float - default is 0, the value should be between 0 to 1)
        corrupt_rate - the probabilities that a message will be corrupted (float - default is 0, the value should be between 0 to 1)
        max_delay - maximum delay for your packet at the server (int - default is 0, the value should be between 0 to 5)

     Output: 
        checksum_val - the checksum value of the file sent (String that always has 5 digits)
    """

    print("Student name: {} {}".format(FIRST_NAME, LAST_NAME))
    print("Start running receiver: {}".format(datetime.datetime.now()))

    checksum_val = "00000"

    #Open a socket connection
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        #Connect to the server
        s.connect((server_ip, server_port))

        #Send message to begin communication with the server
        server_message = 'HELLO R {} {} {} {}'.format(loss_rate, corrupt_rate, max_delay, connection_ID)
        s.send(bytes(server_message, 'utf-8'))

        #Handle server response messages
        while True:
            rcv_message = s.recv(1024).decode('utf-8')
            tokens = rcv_message.split()
            if 'OK' in tokens:
                break
            if 'WAITING' in tokens:
                continue
            else:
                quit()

        #Contains the entire string received after running the FSM
        data = ''

        #Continue to run the loop while the connection has not closed
        while True:

            #Wait for 0 from below - rdt_rcv(rcvpkt)
            rcvpkt = s.recv(30)

            #Stop receiving data once the connection closes
            if not rcvpkt:
                break

            #Set the current sequence number of the receiver
            cur_seq = 0

            #Wait for 0 from below - rdt_rcv(rcvpkt) && (corrupt(rcvpkt) || has_seq1(rcv_pkt))
            if (rcvpkt != None):
                while (corrupt(rcvpkt) or not has_seq(rcvpkt, cur_seq)):


                    #Make the packet and sent it through UDT
                    sndpkt = make_pkt(cur_seq, 1, rcvpkt)
                    s.sendall(sndpkt)

                    #Try to receive the packet again
                    rcvpkt = s.recv(30)

                    #Stop receiving data once the connection closes
                    if not rcvpkt:
                        break

                    #Wait for 0 from below ==> Wait for 1 from below - rdt_rcv(rcvpkt) && notcorrupt(rcvpkt) && has_seq0(rcvpkt)
                    if (not corrupt(rcvpkt) and has_seq(rcvpkt, cur_seq)):
                        break

            #Wait for 0 from below ==> Wait for 1 from below - rdt_rcv(rcvpkt) && notcorrupt(rcvpkt) && has_seq0(rcvpkt)
            if (not corrupt(rcvpkt) and has_seq(rcvpkt, cur_seq)):

                #Extract the data, make a packet with it, and send it through UDT
                data += extract(rcvpkt)
                sndpkt = make_pkt(cur_seq, 0, rcvpkt)
                s.sendall(sndpkt)

            #Change the current sequence number
            cur_seq = 1

            #Wait for 1 from below - rdt_rcv(rcvpkt)
            rcvpkt = s.recv(30)

            #Stop receiving data once the connection closes
            if not rcvpkt:
                break

            #Wait for 1 from below - rdt_rcv(rcvpkt) && (corrupt(rcvpkt) || has_seq1(rcv_pkt))
            if (rcvpkt != None):
                while (corrupt(rcvpkt) or not has_seq(rcvpkt, cur_seq)):

                    #Make the packet and send it through UDT
                    sndpkt = make_pkt(cur_seq, 0, rcvpkt)
                    s.sendall(sndpkt)

                    #Try to receive the packet again
                    rcvpkt = s.recv(30)

                    #Stop receiving data once the connection closes
                    if not rcvpkt:
                        break

                    #Wait for 1 from below ==> Wait for 0 from below - rdt_rcv(rcvpkt) && notcorrupt(rcvpkt) && has_seq0(rcvpkt)
                    if (not corrupt(rcvpkt) and has_seq(rcvpkt, cur_seq)):
                        break


            #Wait for 1 from below ==> Wait for 0 from below - rdt_rcv(rcvpkt) && notcorrupt(rcvpkt) && has_seq0(rcvpkt)
            if (rcvpkt != None):
                if (not corrupt(rcvpkt) and has_seq(rcvpkt, cur_seq)):

                    #Extract the data, make the packet, and send it through UDT
                    data += extract(rcvpkt)
                    sndpkt = make_pkt(cur_seq, 1, rcvpkt)
                    s.sendall(sndpkt)


        #Update the checksum_val
        checksum_val = checksum(data)

    print("Finish running receiver: {}".format(datetime.datetime.now()))

    # PRINT STATISTICS
    print("File checksum: {}".format(checksum_val))

    return checksum_val

 
if __name__ == '__main__':
    # CHECK INPUT ARGUMENTS
    if len(sys.argv) != 7:
        print("Expected \"python PA2_receiver.py <server_ip> <server_port> <connection_id> <loss_rate> <corrupt_rate> <max_delay>\"")
        exit()
    server_ip, server_port, connection_ID, loss_rate, corrupt_rate, max_delay = sys.argv[1:]
    # START RECEIVER
    start_receiver(server_ip, int(server_port), connection_ID, loss_rate, corrupt_rate, max_delay)
