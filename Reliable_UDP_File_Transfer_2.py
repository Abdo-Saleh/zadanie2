import binascii
import socket as sc
import sys
from struct import *
import time
import math
import os
import threading

enable_keep_alive = 0

header = Struct('BBHHHH')
headerSize = calcsize('BBHHHH')
sock_t = ()
supported_file_types_codes = {
    ".txt": 2,
    ".pdf": 3,
    ".jpg": 4
}
current_fileTypeCode = supported_file_types_codes[".txt"]

value = 0

fullText = ""

# fragment was meant to be without header
min_fragment_size = 1
# 1500 - 20 - 8 - 10 = max payload that i can send
max_fragment_size = 1462

enable_loging = True

defaultFileDir = os.getcwd() + "\\Test"

fragment_size = 1

TXT = ".txt"
PDF = ".pdf"
JPG = ".jpg"

keep_alive = True

sleepyReceiver = '0'

# time out 3 sec
time_out = 3
max_number_of_resnding_attempts = 3

currentFileExtention = TXT

serverBuffer = bytearray()

host = "192.168.0.102"
port = 12345
seq = 1

value = 2


# def sendTextAsOnePartOrMulti(textToBeSent):

def senderSocket(host_l, port_l):
    global sock_t
    address = (host_l, int(port_l))
    sock = sc.socket(sc.AF_INET, sc.SOCK_DGRAM)
    sock_t = (sock, address)
    syn_3 = header.pack(2, 1, seq, 0, 0, 0)
    sock.sendto(syn_3, address)
    if enable_loging:
        print("SYN Sent")
    data, address_r = sock.recvfrom(1500)
    returned_value = (data, address_r)
    if returned_value:
        syn_ack_3 = header.unpack(data)
        # if it's ack == 4 and same seq
        if syn_ack_3[0] == 4 and syn_ack_3[2] == seq:
            if enable_loging:
                print("Received a SYN/ACK")
            ack_3 = header.pack(4, 1, seq, 0, 0, 0)
            if enable_loging:
                print("Send ACK ")
            sock.sendto(ack_3, address)
            enable_keep_alive = 1
    return sock, address_r


def receiverSocket():
    global sock_t, enable_loging
    host = "127.0.0.1"
    port = 12345
    address = (host, port)
    sock = sc.socket(sc.AF_INET, sc.SOCK_DGRAM)
    sock_t = (sock, address)
    sock.bind(address)
    print("Waiting for connection...")
    data, address_r = sock.recvfrom(1500)
    if enable_loging:
        print("Connected to Client : {} with his port : {}".format(address_r[0], address_r[1]))

    returned_value = (data, address_r)
    if returned_value:
        syn_3_r = header.unpack(data)
        if syn_3_r[0] == 2:
            if enable_loging:
                print('SYN Received')
            syn_ack_3 = header.pack(4, 1, seq, 0, 0, 0)
            sock.sendto(syn_ack_3, address_r)
            if enable_loging:
                print('Sent SYN/ACK')
        ack_3, address_r = sock.recvfrom(1500)
        if ack_3[0] == 4:
            if enable_loging:
                print('Received ACK')
                print('Connection Established')
    return sock, address_r


def fin_connection_m(sock, address_r):
    global enable_keep_alive, value, seq
    enable_keep_alive = 0
    value = 8
    seq = 1
    fin_connection = header.pack(8, 1, 0, 0, 0, 0)
    sock.sendto(fin_connection, address_r)
    data, address_r = sock.recvfrom(1500)
    fin_connection = header.unpack(data)
    if fin_connection[0] == 4:
        return value
    else:
        if enable_loging:
            print("Unexpected Behaviour")

    enable_keep_alive = 1


def sender(sock, address_r):
    global seq, fragment_size, time_out, defaultFileDir, current_fileTypeCode, enable_keep_alive, value, max_number_of_resnding_attempts
    print('Mode is Sender ...')
    seq = 1
    status = True
    while status:
        # connection established
        print("1- Text")
        print("2- File")
        print("3- Switch Mode ? :")
        print("4- Close connection ? :")
        # measure for the time, if greater than 1 sec, send keep-alive
        menu = input("Choose what would like to send : ")

        if menu == '1' or menu == '2':
            try:
                fragment_size = int(input('Please enter fragment size which must be bigger than {} and less than {} :'
                                          .format(min_fragment_size, max_fragment_size)))
            except:
                print("Unexpected Error")
                value = fin_connection_m(sock, address_r)
                return value

        while fragment_size < min_fragment_size or fragment_size > max_fragment_size:
            try:
                fragment_size = int(input(
                    'You have entered  a bad fragment size, please make sure to enter a value bigger than {} and less '
                    'than {} : '
                        .format(min_fragment_size, max_fragment_size)))
            except:
                print("Unexpected Error")
                value = fin_connection_m(sock, address_r)
                return value
        if menu == '1':
            enable_keep_alive = 0
            if enable_loging:
                print("Sending Text ......")
            textToBeSent = input("Enter the text would you like to send safely : ")
            # is it necessary to fragment the text
            lengthOfTheText = len(textToBeSent)
            # if no, send normally
            if lengthOfTheText <= fragment_size:
                # if no, send normally
                isItWithinTimeOut = False
                number_of_resending_attempts = 1
                while not isItWithinTimeOut:
                    data = textToBeSent.encode()
                    crcValue = binascii.crc_hqx(data, 0)
                    seq = seq + 1
                    head = header.pack(2, 1, seq, 1, lengthOfTheText, crcValue)
                    packet = b"".join([head, data])
                    sock.sendto(packet, address_r)

                    start_exec = time.time()
                    if enable_loging:
                        print('Text has been sent')

                    packet, address_r = sock.recvfrom(1500)
                    end_exec = time.time()

                    if int(
                            end_exec - start_exec) <= time_out:
                        isItWithinTimeOut = True
                    else:
                        number_of_resending_attempts += 1
                        isItWithinTimeOut = False
                        print('Text is being resent coz it exceeded the timeout')

                    if number_of_resending_attempts >= max_number_of_resnding_attempts:
                        value = fin_connection_m(sock, address_r)
                        print("Destination has some problems")
                        return value

                headerInfo = header.unpack(packet[:headerSize])
                wasItSentSuccessfully = False
                while not wasItSentSuccessfully:
                    if headerInfo[0] == 4:
                        # received ack on the sent text
                        if enable_loging:
                            print('Text has been received at the receiver successfully')
                        wasItSentSuccessfully = True
                    elif headerInfo[0] == 0:
                        if enable_loging:
                            print('Text has been received with problems')
                            print('The Text is being resent again')
                        sock.sendto(packet, address_r)
                        packet, address_r = sock.recvfrom(1500)
                        headerInfo = header.unpack(packet[:headerSize])
                    else:
                        if enable_loging:
                            print('Text has been received with some thing idk')
            else:
                # if yes, we need fragmentation and sending it one by one
                if enable_loging:
                    print('we need fragmentation so we send it one by one')
                numberOfNeededFragments = math.ceil((lengthOfTheText / fragment_size))
                seq = 1
                while seq <= numberOfNeededFragments:
                    isItWithinTimeOut = False
                    number_of_resending_attempts = 1
                    while not isItWithinTimeOut:
                        start_exec = time.time()
                        start = (seq - 1) * fragment_size
                        end = seq * fragment_size
                        data = textToBeSent[start:end].encode()
                        crcValue = binascii.crc_hqx(data, 0)
                        head = header.pack(2, 1, seq, numberOfNeededFragments, len(data), crcValue)
                        packet = b"".join([head, data])
                        sock.sendto(packet, address_r)
                        packet_r, address_r = sock.recvfrom(1500)
                        end_exec = time.time()

                        if int(
                                end_exec - start_exec) <= time_out:
                            isItWithinTimeOut = True
                        else:
                            number_of_resending_attempts += 1
                            isItWithinTimeOut = False
                            print('Fragment {} is being resent coz it exceeded the timeout'.format(seq))

                        if number_of_resending_attempts >= max_number_of_resnding_attempts:
                            value = fin_connection_m(sock, address_r)
                            print("Destination has some problems")
                            return value

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
                            print('The Fragment {} has been received with unexpected state'.format(seq))
                if (seq - 1) == numberOfNeededFragments:
                    if enable_loging:
                        print("The text has been received successfully")
                else:
                    if enable_loging:
                        print("The text has been received with errors")
            enable_keep_alive = 1

        elif menu == '2':
            enable_keep_alive = 0
            enable_simulation = input("Would you like to simulate of file transfer error, (Y)es, (N)o ")

            if enable_simulation == "Y":
                print("Some random data would be inserted instead of a real packet")

            print("Sending File ........")
            filelocation = input(
                "Enter the File location where your file exits (Default) {}:".format(defaultFileDir))
            if len(filelocation) == 0:
                filelocation = defaultFileDir
            fileName = input("Enter the File name which you would like to send safely:")
            fileTypeCode = supported_file_types_codes['.txt']
            try:
                tmpLoc = filelocation + '\\' + fileName
                f = open(tmpLoc, "rb")
                filename, file_extension = os.path.splitext(tmpLoc)
                current_fileTypeCode = supported_file_types_codes[file_extension]
                fileContent = f.read()
                f.close()
            except IOError:
                print("Error: File does not appear to exist.")
                continue
            # first sending the file name
            if enable_loging:
                print("File name is being sent ....")

            lengthOfTheFileName = len(fileName)
            if len(fileContent) + lengthOfTheFileName <= fragment_size:

                isItWithinTimeOut = False
                number_of_resending_attempts = 1
                while not isItWithinTimeOut:
                    start_exec = time.time()
                    # basically we can send the file name with its content in one fragment
                    fragment = bytearray()
                    # data = fileName.encode()
                    fragment.extend(fileName.encode())
                    fragment.extend(fileContent)
                    crcValue = binascii.crc_hqx(fragment, 0)
                    seq = seq + 1
                    head = header.pack(2, current_fileTypeCode, seq, 1, len(fileContent) + lengthOfTheFileName,
                                       crcValue)

                    if enable_simulation == "Y":
                        fileName_s = fileName + str(int(time.time()))
                        fragment = bytearray()
                        # data = fileName.encode()
                        fragment.extend(fileName_s.encode())
                        fragment.extend(fileContent)

                    packet = b"".join([head, fragment])
                    sock.sendto(packet, address_r)
                    if enable_loging:
                        print('File has been sent as one fragment')
                    packet, address_r = sock.recvfrom(1500)
                    end_exec = time.time()

                    if int(
                            end_exec - start_exec) <= time_out:
                        isItWithinTimeOut = True
                    else:
                        number_of_resending_attempts += 1
                        isItWithinTimeOut = False
                        print('The File is being resent coz it exceeded the timeout')

                    if number_of_resending_attempts >= max_number_of_resnding_attempts:
                        value = fin_connection_m(sock, address_r)
                        print("Destination has some problems")
                        return value

                headerInfo = header.unpack(packet[:headerSize])
                wasItSentSuccessfully = False
                while not wasItSentSuccessfully:
                    if headerInfo[0] == 4:
                        # received ack on the sent fragment
                        if enable_loging:
                            print('File has been received at the receiver successfully')
                        wasItSentSuccessfully = True
                    elif headerInfo[0] == 0:
                        if enable_loging:
                            print('File has been received with problems')
                            print('The File is being resent again')

                        if enable_simulation == "Y":
                            fragment = bytearray()
                            fragment.extend(fileName.encode())
                            fragment.extend(fileContent)
                            crcValue = binascii.crc_hqx(fragment, 0)

                        head = header.pack(2, current_fileTypeCode, seq, 1,
                                           len(fileContent) + lengthOfTheFileName,
                                           crcValue)
                        packet = b"".join([head, fragment])

                        # fix the error and resend it
                        sock.sendto(packet, address_r)

                        packet, address_r = sock.recvfrom(1500)
                        headerInfo = header.unpack(packet[:headerSize])
                        if headerInfo[0] == 4:
                            wasItSentSuccessfully = True
                    else:
                        if enable_loging:
                            print('Text has been received with some thing idk')
            else:
                # it must be fragmented
                if enable_loging:
                    print('we need fragmentation and sending it one by one')
                numberOfNeededFragments = math.ceil(
                    ((len(fileContent) + lengthOfTheFileName) / fragment_size))
                seq = 1

                fileNameWithContent = bytearray()
                fileNameWithContent.extend(fileName.encode())
                fileNameWithContent.extend(fileContent)
                while seq <= numberOfNeededFragments:
                    isItWithinTimeOut = False
                    number_of_resending_attempts = 1

                    while not isItWithinTimeOut:
                        start_exec = time.time()
                        start = (seq - 1) * fragment_size
                        end = seq * fragment_size
                        fragment = fileNameWithContent[start:end]
                        crcValue = binascii.crc_hqx(fragment, 0)
                        head = header.pack(2, current_fileTypeCode, seq, numberOfNeededFragments, len(fragment),
                                           crcValue)
                        packet = b"".join([head, fragment])

                        sock.sendto(packet, address_r)

                        packet_r, address_r = sock.recvfrom(1500)
                        end_exec = time.time()
                        if int(
                                end_exec - start_exec) <= time_out:
                            isItWithinTimeOut = True
                        else:
                            number_of_resending_attempts += 1
                            isItWithinTimeOut = False
                            print('Fragment {} is being resent coz it exceeded the timeout'.format(seq))

                        if number_of_resending_attempts >= max_number_of_resnding_attempts:
                            value = fin_connection_m(sock, address_r)
                            print("Destination has some problems")
                            return value

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
                            print('The Fragment {} has been received with unexpected state'.format(seq))
                if (seq - 1) == numberOfNeededFragments:
                    print("The text has been received successfully")
                else:
                    print("The text has been received with errors")
            enable_keep_alive = 1
        elif menu == '3':
            value = fin_connection_m(sock, address_r)
            return value
        elif menu == '4':
            enable_keep_alive = 0
            value = 16
            if enable_loging:
                print("I am going away now, thank you")
                print("Sending close connection request")
            close_connection = header.pack(16, 1, 0, 0, 0, 0)
            sock.sendto(close_connection, address_r)
            data, address_r = sock.recvfrom(1500)
            close_connection = header.unpack(data)
            if enable_loging:
                print("I have received ack on your close connection request, See you again ")
            if close_connection[0] == 4:
                try:
                    return value
                except:
                    if enable_loging:
                        print("I was trying my best to close this connection, but it seems you liked me, and i cannot "
                              "leave you alone")
                    continue
            else:
                if enable_loging:
                    print("Unexpected Behaviour")
                continue


def receiver(sock, address_r):
    global seq, fragment_size, headerSize, fullText, currentFileExtention, serverBuffer, value, sleepyReceiver

    print('Mode is Receiver ...')
    print("Waiting to receive packets")
    sleepyReceiver = input("Would you like to simulate a hangovered Receiver (1 or 0) : ")

    while True:
        packet, address = sock.recvfrom(1500)

        if sleepyReceiver == '1':
            time.sleep(5)

        headerInfo = header.unpack(packet[:headerSize])
        numberOfexpectedFragments = headerInfo[3]
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
                        if enable_loging:
                            print("Sent Ack state for the text {}".format(fullText))
                    else:
                        head = header.pack(0, 1, headerInfo[2], headerInfo[3], headerInfo[4],
                                           headerInfo[5])
                        packet = b"".join([head, textToBeReceived])

                        sock.sendto(packet, address_r)
                        if enable_loging:
                            print("Sent invalid state for the text")
                        packet, address = sock.recvfrom(1500)
                        headerInfo = header.unpack(packet[:headerSize])
                        textToBeReceived = packet[headerSize:]
                        crc_for_received_text = binascii.crc_hqx(textToBeReceived, 0)
                fullText = ""
            else:
                # test unearchable Receiver
                # time.sleep(10)
                # it's more than one fragment text
                seq = headerInfo[2]
                start_exec = time.time()
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
                        if enable_loging:
                            print("Sent Ack state for the fragment {}".format(headerInfo[2]))
                    else:
                        head = header.pack(0, 1, headerInfo[2], headerInfo[3], headerInfo[4],
                                           headerInfo[5])
                        packet = b"".join([head, fragmentToBeReceived])

                        sock.sendto(packet, address_r)
                        if enable_loging:
                            print("Sent invalid state for the fragment {}".format(headerInfo[2]))
                        packet, address = sock.recvfrom(1500)
                        headerInfo = header.unpack(packet[:headerSize])
                        fragmentToBeReceived = packet[headerSize:]
                        # fullText += fragmentToBeReceived.decode()
                        crc_for_received_fragment = binascii.crc_hqx(fragmentToBeReceived, 0)

                if seq < numberOfexpectedFragments:
                    if enable_loging:
                        print("The text is being downloaded")
                elif seq == numberOfexpectedFragments:
                    if enable_loging:
                        print("The text has been received successfully {}".format(fullText))
                    fullText = ""
                else:
                    if enable_loging:
                        print("Unexpected Behaviour")

        elif headerInfo[0] == 2:
            if headerInfo[1] == 2:
                currentFileExtention = TXT
            elif headerInfo[1] == 3:
                currentFileExtention = PDF
            elif headerInfo[1] == 4:
                currentFileExtention = JPG
            else:
                currentFileExtention
            # receiving .txt file
            if headerInfo[3] == 1:
                seq = headerInfo[2]
                # File name was sent as one part
                if enable_loging:
                    print("File is being recevied as one part ....")
                fileToBeRecevied = packet[headerSize:]
                crc_for_received_file = binascii.crc_hqx(fileToBeRecevied, 0)
                wasItReceivedSuccessfully = False
                fileAtRecevier = bytearray()
                fileAtRecevier.extend(packet[headerSize:])
                while not wasItReceivedSuccessfully:
                    if crc_for_received_file == headerInfo[5]:
                        head = header.pack(4, headerInfo[1], headerInfo[2], headerInfo[3], headerInfo[4],
                                           headerInfo[5])
                        packet = b"".join([head, fileToBeRecevied])
                        wasItReceivedSuccessfully = True
                        sock.sendto(packet, address_r)
                        receivedFragment = fileAtRecevier.decode().split(".")
                        fileNameAtRecevier = receivedFragment[0]
                        fileContent = receivedFragment[1][len(currentFileExtention) - 1:]
                        try:
                            f = open(fileNameAtRecevier + currentFileExtention, 'wb')
                        except:
                            f = open('file' + str(int(time.time())), 'wb')
                            if enable_loging:
                                print("File can't be created at this location {} \\ {}".format(os.getcwd(),
                                                                                               fileNameAtRecevier))
                        payloadToBeWritten = bytearray()
                        payloadToBeWritten.extend(fileContent.encode())
                        f.write(payloadToBeWritten)
                        f.close()
                        if enable_loging:
                            print("this is the file at the server ", fileNameAtRecevier)
                            print("this is the file extention at the server ", currentFileExtention)
                            print("Sent Ack state for the file {} packet".format(
                                fileNameAtRecevier + currentFileExtention))
                    else:
                        head = header.pack(0, headerInfo[1], headerInfo[2], headerInfo[3], headerInfo[4],
                                           headerInfo[5])

                        packet = b"".join([head, fileAtRecevier])
                        sock.sendto(packet, address_r)
                        wasItReceivedSuccessfully = True
                        if enable_loging:
                            print(header.unpack(head))
                            print(packet[headerSize:])
                            print("Sent invalid state for the file fragment")
                    fileAtRecevier = bytearray()
            else:
                # file is being transfered by multi fragments
                seq = headerInfo[2]
                start_exec = time.time()
                fragmentToBeReceived = packet[headerSize:]
                crc_for_received_fragment = binascii.crc_hqx(fragmentToBeReceived, 0)
                wasItReceivedSuccessfully = False
                while not wasItReceivedSuccessfully:
                    if crc_for_received_fragment == headerInfo[5]:
                        head = header.pack(4, headerInfo[1], headerInfo[2], headerInfo[3], headerInfo[4],
                                           headerInfo[5])
                        packet = b"".join([head, fragmentToBeReceived])
                        wasItReceivedSuccessfully = True
                        sock.sendto(packet, address_r)
                        serverBuffer.extend(fragmentToBeReceived)
                        if enable_loging:
                            print("Sent Ack state for the fragment {}".format(headerInfo[2]))
                    else:
                        head = header.pack(0, headerInfo[1], headerInfo[2], headerInfo[3], headerInfo[4],
                                           headerInfo[5])
                        packet = b"".join([head, fragmentToBeReceived])
                        sock.sendto(packet, address_r)
                        if enable_loging:
                            print("Sent invalid state for the fragment {}".format(headerInfo[2]))

                if seq < numberOfexpectedFragments and enable_loging:
                    print("The file is being downloaded")
                elif seq == numberOfexpectedFragments:
                    receivedFile = serverBuffer
                    fileNameAtRecevier = ""
                    fileContent = bytearray()
                    if currentFileExtention == '.pdf' or currentFileExtention == '.jpg':
                        x = extractFileInfoFromPdfJpg(serverBuffer)
                        fileNameAtRecevier = serverBuffer[:x].decode()
                        fileContent = serverBuffer[x + 4:]
                    else:
                        receivedFile = serverBuffer.decode().split(".")
                        fileNameAtRecevier = receivedFile[0]
                        fileContent = receivedFile[1][len(currentFileExtention) - 1:]
                    if enable_loging:
                        print("The file has been received successfully")
                    try:
                        f = open(fileNameAtRecevier + currentFileExtention, 'wb')
                        if currentFileExtention == '.pdf' or currentFileExtention == '.jpg':
                            f.write(fileContent)
                        else:
                            f.write(fileContent.encode())
                        f.close()
                        serverBuffer = bytearray()
                    except:
                        f = open('file' + str(int(time.time())), 'wb')
                        if enable_loging:
                            print("File can't be created at this location {} \\ {}".format(os.getcwd(),
                                                                                           fileNameAtRecevier))
                else:
                    if enable_loging:
                        print("Unexpected Behaviour")
        elif headerInfo[0] == 14:
            keep_alive_pckt = header.pack(14, 1, 0, 0, 0, 0)
            sock.sendto(keep_alive_pckt, address)
        elif headerInfo[0] == 8:
            fin_connection_ack = header.pack(4, 1, 0, 0, 0, 0)
            sock.sendto(fin_connection_ack, address)
            value = 8
            return value
        elif headerInfo[0] == 16:
            if enable_loging:
                print("I have received, that you want to release me !!")
                print("Anyway it's life, see you one time, next time, oh no we're alive ? bye !!")
            close_connection_ack = header.pack(4, 1, 0, 0, 0, 0)
            sock.sendto(close_connection_ack, address)
            value = 16
            return value


def extractFileInfoFromPdfJpg(buffer):
    foundAtIndex = -1
    for x in range(0, len(buffer), 1):
        if buffer[x:x + 4].decode() == '.pdf' or buffer[x:x + 4].decode() == '.jpg':
            foundAtIndex = x
            break
        else:
            foundAtIndex = -1
    return foundAtIndex


start = time.time()


def run_keep_alive():
    global enable_keep_alive, sock_t
    while True:
        if enable_keep_alive == 1:
            try:
                keep_alive_pckt = header.pack(14, 1, 0, 0, 0, 0)
                sock_t[0].sendto(keep_alive_pckt, sock_t[1])
                if enable_loging:
                    print("Alive")
                packet, address_r = sock_t[0].recvfrom(1500)
            except:
                if enable_loging:
                    print("Alive")
                print("sock not init")
        time.sleep(3)


def my_inline_function():
    # do some stuff
    download_thread = threading.Thread(target=run_keep_alive, name="keep-alive")
    download_thread.daemon = True
    download_thread.start()

    # continue doing stuff


def main():
    global min_fragment_size, max_fragment_size, enable_keep_alive, value, enable_loging
    # print("1- Server")
    # print("2- Client")
    #
    # my_inline_function()
    # while True:
    #     mode = input("Please choose your mode (1 or 2): ")
    #     if mode == "1":
    #         sock, address = receiverSocket()
    #         receiver(sock,address)
    #         break
    #     elif mode == "2":
    #         host_l = input('Please enter destination address:  ')
    #         port_l = input('Please enter destination port:  ')
    #         sock, address = senderSocket(host_l,port_l)
    #         sender(sock,address)
    #         break
    #     else:
    #         print("You've entered a bad mode, please choose correctly")

    my_inline_function()
    status = True
    while status:
        try:
            status = False
            print("1- Server")
            print("2- Client")
            mode = int(input("Please choose your mode: "))

            enable_loging = int(input("Would you like to enable logging 1 or 0 :"))
        except:
            status = True
            continue
    #
    # if mode == 1 or mode == 2:
    #     thread.start()

    if mode == 1:
        sock, address = receiverSocket()

        while value != 16:
            print("1- Sender")
            print("2- Recevier")
            choice = int(input('Please choose your mode : '))
            value = 2
            while value != 8 and value != 16:
                if choice == 2:
                    value = receiver(sock, address)
                elif choice == 1:
                    value = sender(sock, address)
                else:
                    print("You have entered bad mode ")

    elif mode == 2:
        host_m = input('Please enter destination address:  ')
        port_m = input('Please enter destination port:  ')
        sock, address = senderSocket(host_m, port_m)
        address_m = (host_m, int(port_m))

        while value != 16:
            print("1- Sender")
            print("2- Recevier")
            choice = int(input('Please choose your mode : '))
            value = 2
            while value != 8 and value != 16:
                if choice == 2:
                    value = receiver(sock, address)
                elif choice == 1:
                    value = sender(sock, address)
                else:
                    print("You have entered bad mode ")

    else:
        print('You have entered bad mode')

    return 0


if __name__ == "__main__":
    main()
