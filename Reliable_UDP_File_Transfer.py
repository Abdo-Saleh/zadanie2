import binascii
import socket as sc
import sys
from struct import *
import time
import math

header = Struct('BBHHHH')
headerSize = calcsize('BBHHHH')

fullText = ""

# fragment was meant to be without header
min_fragment_size = 1
# 1500 - 20 - 8 - 10 = max payload that i can send
max_fragment_size = 1462

fragment_size = 1

keep_alive = True

# time out 3 sec
time_out = 3

buffer = {}

host = "127.0.0.1"
port = 55555
seq = 1


def keepAlive(sock, address, mode):
    start_execuation = time.time()
    global keep_alive
    time.sleep(1)
    if mode == "c":
        keepAlive_packet_send = header.pack(12, 1, 0, 0, 0, 0)
        sock.sendto(keepAlive_packet_send, address)
        print("A keep alive packet is being sent from sender every 1 sec")
        if time.time() - 10 < start_execuation:
            data, address_r = sock.recvfrom(1500)
            headerInfo = header.unpack(data)
            if headerInfo[0] == 12:
                keep_alive = True
                start_execuation = time.time()
        else:
            keep_alive = False


    elif mode == "s":
        if time.time() - 10 < start_execuation:
            data, address_r = sock.recvfrom(1500)
            headerInfo = header.unpack(data)
            if headerInfo[0] == 12:
                keepAlive_packet_send = header.pack(12, 1, 0, 0, 0, 0)
                sock.sendto(keepAlive_packet_send, address)
                print("A keep alive packet is being sent from the receiver every 1 sec")
                keep_alive = True
                start_execuation = time.time()
            else:
                keep_alive = False

        return keep_alive


def sender():
    global seq, fragment_size, time_out
    print('Mode is Sender ...')
    host_l = input('Please enter destination address:  ')
    port_l = input('Please enter destination port:  ')
    address = (host_l, int(port_l))
    fragment_size = int(input('Please enter fragment size which must be bigger than {} and less than {} :'
                              .format(min_fragment_size, max_fragment_size)))

    while fragment_size < min_fragment_size or fragment_size > max_fragment_size:
        fragment_size = int(input(
            'You have entered  a bad fragment size, please make sure to enter a value bigger than {} and less than {} :'
                .format(min_fragment_size, max_fragment_size)))

    sock = sc.socket(sc.AF_INET, sc.SOCK_DGRAM)
    syn_3 = header.pack(2, 1, seq, 0, 0, 0)
    sock.sendto(syn_3, address)
    print("SYN Sent")
    data, address_r = sock.recvfrom(1500)
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
                    # if no, send normally
                    if lengthOfTheText <= fragment_size:
                        # if no, send normally
                        data = textToBeSent.encode()
                        crcValue = binascii.crc_hqx(data, 0)
                        seq = seq + 1
                        head = header.pack(2, 1, seq, 1, lengthOfTheText, crcValue)
                        packet = b"".join([head, data])
                        sock.sendto(packet, address_r)
                        print('Text has been sent')
                        packet, address_r = sock.recvfrom(1500)
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
                                packet, address_r = sock.recvfrom(1500)
                                headerInfo = header.unpack(packet[:headerSize])
                            else:
                                print('Text has been received with some thing idk')

                    else:
                        # if yes, we need fragmentation and sending it one by one
                        print('we need fragmentation and sending it one by one')
                        numberOfNeededFragments = math.ceil((lengthOfTheText / fragment_size))
                        seq = 1
                        start_exec = time.time()
                        while seq <= numberOfNeededFragments:
                            start = (seq - 1) * fragment_size
                            end = seq * fragment_size
                            data = textToBeSent[start:end].encode()
                            crcValue = binascii.crc_hqx(data, 0)
                            head = header.pack(2, 1, seq, numberOfNeededFragments, len(data), crcValue)
                            packet = b"".join([head, data])
                            sock.sendto(packet, address_r)

                            if int(time.time() - start_exec) >= time_out:
                                seq = 1
                                print("Destination unreachable")
                                sys.exit()

                            packet_r, address_r = sock.recvfrom(1500)

                            headerInfo = header.unpack(packet_r[:headerSize])
                            wasItSentSuccessfully = False
                            while not wasItSentSuccessfully:
                                if headerInfo[0] == 4:
                                    # received ack on the sent text
                                    print('Fragment {} has been received at the receiver successfully'.format(seq))
                                    wasItSentSuccessfully = True
                                    seq += 1
                                elif headerInfo[0] == 0:
                                    print('Fragment {} has been received with problems'.format(seq))
                                    print('The Fragment {} is being resent again'.format(seq))
                                    sock.sendto(packet, address_r)
                                    packet, address_r = sock.recvfrom(1500)
                                    headerInfo = header.unpack(packet[:headerSize])
                                else:
                                    print('The Fragment {} has been received unexpected state'.format(seq))

                    if seq == numberOfNeededFragments:
                        print("The text has been received successfully")
                    else:
                        print("The text has been received with errors")


def receiver():
    print('Mode is Receiver ...')
    global host, port, seq, fragment_size, headerSize, fullText
    address = (host, port)
    sock = sc.socket(sc.AF_INET, sc.SOCK_DGRAM)
    sock.bind(address)
    print("Waiting for connection...")
    data, address_r = sock.recvfrom(1500)
    returned_value = (data, address_r)
    if returned_value:
        syn_3_r = header.unpack(data)
        if syn_3_r[0] == 2:
            print('SYN Received')
            syn_ack_3 = header.pack(4, 1, seq, 0, 0, 0)
            sock.sendto(syn_ack_3, address_r)
            print('Sent SYN/ACK')
        ack_3, address_r = sock.recvfrom(1500)
        if ack_3[0] == 4:
            print('Received ACK')
            print('Connection Established')
            print("Waiting to receive packets")
            while True:
                packet, address = sock.recvfrom(1500)
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
                                fullText = textToBeReceived.decode()
                                print("Sent Ack state for the text {}".format(fullText))
                            else:
                                head = header.pack(0, 1, headerInfo[2], headerInfo[3], headerInfo[4],
                                                   headerInfo[5])
                                packet = b"".join([head, textToBeReceived])

                                sock.sendto(packet, address_r)
                                print("Sent invalid state for the text")
                                packet, address = sock.recvfrom(1500)
                                headerInfo = header.unpack(packet[:headerSize])
                                textToBeReceived = packet[headerSize:]
                                crc_for_received_text = binascii.crc_hqx(textToBeReceived, 0)
                    else:
                        # test unearchable Receiver
                        # time.sleep(10)
                        # it's more than one fragment text
                        seq = headerInfo[2]
                        start_exec = time.time()
                        numberOfexpectedFragments = headerInfo[3]
                        fragmentToBeReceived = packet[headerSize:]
                        crc_for_received_fragment = binascii.crc_hqx(fragmentToBeReceived, 0)
                        wasItReceivedSuccessfully = False
                        while not wasItReceivedSuccessfully:
                            if crc_for_received_fragment == headerInfo[5]:
                                head = header.pack(4, 1, headerInfo[2], headerInfo[3], headerInfo[4], headerInfo[5])
                                packet = b"".join([head, fragmentToBeReceived])
                                wasItReceivedSuccessfully = True
                                sock.sendto(packet, address_r)
                                fullText += fragmentToBeReceived.decode()
                                print("Sent Ack state for the fragment {}".format(headerInfo[2]))
                            else:
                                head = header.pack(0, 1, headerInfo[2], headerInfo[3], headerInfo[4],
                                                   headerInfo[5])
                                packet = b"".join([head, fragmentToBeReceived])

                                sock.sendto(packet, address_r)
                                print("Sent invalid state for the fragment {}".format(headerInfo[2]))
                                packet, address = sock.recvfrom(1500)
                                headerInfo = header.unpack(packet[:headerSize])
                                fragmentToBeReceived = packet[headerSize:]
                                fullText += fragmentToBeReceived.decode()
                                crc_for_received_fragment = binascii.crc_hqx(fragmentToBeReceived, 0)

                    print(fullText)
                    if seq == numberOfexpectedFragments:
                        print("The text has been received successfully")
                    else:
                        print("The text has been received with errors")


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
