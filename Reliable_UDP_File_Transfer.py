import binascii
import socket as sc
from struct import *
import time

header = Struct('BBHHHH')
headerSize = calcsize('BBHHHH')

min_fragment_size = 48
max_fragment_size = 1452

fragment_size = 48

keep_alive = True

buffer = {}

host = "127.0.0.1"
port = 55555
seq = 1


def keepAlive(sock, address, mode):
    global keep_alive
    while keep_alive:
        time.sleep(1)
        if mode == "c":
            keepAlive_packet_send = header.pack(12, 1, 0, 0, 0, 0)
            sock.sendto(keepAlive_packet_send, address)
            print("A keep alive packet is being sent from sender every 1 sec")
            data, address_r = sock.recvfrom(1518)
            headerInfo = header.unpack(data)
            if headerInfo[0] == 12:
                keep_alive = True
            elif headerInfo[0] == 8:
                # fin the connection
                keep_alive = False
            else:
                keep_alive = False

        elif mode == "s":
            data, address_r = sock.recvfrom(1518)
            headerInfo = header.unpack(data)
            if headerInfo[0] == 12:
                keepAlive_packet_send = header.pack(12, 1, 0, 0, 0, 0)
                sock.sendto(keepAlive_packet_send, address)
                print("A keep alive packet is being sent from the receiver every 1 sec")
                keep_alive = True
            elif headerInfo[0] == 8:
                # fin the connection
                keep_alive = False
            else:
                keep_alive = False


def sender():
    global seq, fragment_size
    print('Mode is Sender ...')
    host_l = input('Please enter destination address:  ')
    port_l = input('Please enter destination port:  ')
    address = (host_l, int(port_l))
    fragment_Size = int(input('Please enter fragment size which must be bigger than {} and less than {}'
                              .format(min_fragment_size, max_fragment_size)))

    while fragment_Size < min_fragment_size or fragment_Size > max_fragment_size:
        fragment_Size = int(input(
            'You have entered  a bad fragment size, please make sure to enter a value bigger than {} and less than {}'
                .format(min_fragment_size, max_fragment_size)))

    sock = sc.socket(sc.AF_INET, sc.SOCK_DGRAM)
    syn_3 = header.pack(2, 1, seq, 0, 0, 0)
    sock.sendto(syn_3, address)
    print("SYN Sent")
    data, address_r = sock.recvfrom(1518)
    returned_value = (data, address_r)
    if returned_value:
        syn_ack_3 = header.unpack(data)
        # if it's ack == 4 and same seq
        if syn_ack_3[0] == 4 and syn_ack_3[2] == seq:
            print("Received a SYN/ACK")
            ack_3 = header.pack(4, 1, seq, 0, 0, 0)
            print("Send ACK ")
            sock.sendto(ack_3, address)
            while True:
                # connection established
                print("1 -Text")
                print("2 -File")
                menu = int(input("Choose what would like to send : "))
                if menu == 1:
                    print("Sending Text")
                    textToBeSent = input("Enter the text would you like to send safely : ")
                    # is it necessary to fragment the text
                    lengthOfTheText = len(textToBeSent)
                    print(lengthOfTheText)
                    # if no, send normally
                    if lengthOfTheText <= (fragment_Size - headerSize):
                        # if no, send normally
                        data = textToBeSent.encode()
                        crcValue = binascii.crc_hqx(data, 0)
                        seq = seq + 1
                        head = header.pack(2, 1, seq, 1, lengthOfTheText, crcValue)
                        packet = b"".join([head, data])
                        sock.sendto(packet, address_r)
                        print('Text has been sent')
                        packet, address_r = sock.recvfrom(fragment_size)
                        headerInfo = header.unpack(packet[:headerSize])
                        wasItSentSuccessfully = False
                        while not wasItSentSuccessfully:
                            if headerInfo[0] == 4:
                                # received ack on the sent text
                                print('Text has been received at the receiver successfully')
                                wasItSentSuccessfully = True
                            elif headerInfo[0] == 0:
                                print('Text has been received with problems')
                                print('The Text is being resent again')
                                sock.sendto(packet, address_r)
                                packet, address_r = sock.recvfrom(fragment_size)
                                headerInfo = header.unpack(packet[:headerSize])
                            else:
                                print('Text has been received with some thing idk')

                    else:
                        # if yes, we need fragmentation and sending it one by one
                        print('we need fragmentation and sending it one by one')


def receiver():
    print('Mode is Receiver ...')
    global host, port, seq, fragment_size, headerSize
    address = (host, port)
    sock = sc.socket(sc.AF_INET, sc.SOCK_DGRAM)
    sock.bind(address)
    print("Waiting for connection...")
    data, address_r = sock.recvfrom(1518)
    returned_value = (data, address_r)
    if returned_value:
        syn_3_r = header.unpack(data)
        if syn_3_r[0] == 2:
            print('SYN Received')
            syn_ack_3 = header.pack(4, 1, seq, 0, 0, 0)
            sock.sendto(syn_ack_3, address_r)
            print('Sent SYN/ACK')
        ack_3, address_r = sock.recvfrom(1518)
        if ack_3[0] == 4:
            print('Received ACK')
            print('Connection Established')
            print("Waiting to receive packets")
            while True:
                packet, address = sock.recvfrom(fragment_size)
                headerInfo = header.unpack(packet[:headerSize])
                if headerInfo[0] == 2 and headerInfo[1] == 1:
                    # we are receving a text file
                    # check whether it's fragmented or not
                    if headerInfo[3] == 1:
                        # it's one fragment text
                        textToBeReceived = packet[headerSize:]
                        crc_for_received_text = binascii.crc_hqx(textToBeReceived, 0)
                        # two cases, first the crc is equal so the text has been received successfully (send ack),
                        # or not then (send invalid)
                        wasItReceivedSuccessfully = False
                        while not wasItReceivedSuccessfully:
                            if crc_for_received_text == headerInfo[5]:
                                head = header.pack(4, 1, headerInfo[2], headerInfo[3], headerInfo[4], headerInfo[5])
                                packet = b"".join([head, textToBeReceived])
                                wasItReceivedSuccessfully = True
                                sock.sendto(packet, address_r)
                                print("Sent Ack state for the text {}".format(textToBeReceived.decode()))
                            else:
                                head = header.pack(0, 1, headerInfo[2], headerInfo[3], headerInfo[4],
                                                   headerInfo[5])
                                packet = b"".join([head, textToBeReceived])

                                sock.sendto(packet, address_r)
                                print("Sent invalid state for the text")
                                packet, address = sock.recvfrom(fragment_size)
                                headerInfo = header.unpack(packet[:headerSize])
                                textToBeReceived = packet[headerSize:]
                                crc_for_received_text = binascii.crc_hqx(textToBeReceived, 0)


def main():
    global min_fragment_size, max_fragment_size
    mode = input("Please choose your mode: ")
    if mode == "server":
        receiver()
    elif mode == "client":
        sender()
    else:
        print("abdo")

    return


if __name__ == "__main__":
    main()
