import binascii
import socket as sc
import sys
from struct import *
import time
import math
import os


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

# time out 3 sec
time_out = 30
currentFileExtention = TXT

serverBuffer = bytearray()

host = "127.0.0.1"
port = 12345
seq = 1

# def sendTextAsOnePartOrMulti(textToBeSent):

def senderSocket():
    return

def receiverSocket(address, port):

    return

def sender():
    global seq, fragment_size, time_out, defaultFileDir, current_fileTypeCode, enable_keep_alive,sock_t
    print('Mode is Sender ...')
    host_l = input('Please enter destination address:  ')
    port_l = input('Please enter destination port:  ')
    address = (host_l, int(port_l))

    sock = sc.socket(sc.AF_INET, sc.SOCK_DGRAM)
    sock_t = (sock,address)
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
            enable_keep_alive = 1
            while True:
                # connection established
                print("1 -Text")
                print("2 -File")
                 # measure for the time, if greater than 1 sec, send keep-alive
                menu = input("Choose what would like to send : ")

                fragment_size = int(input('Please enter fragment size which must be bigger than {} and less than {} :'
                                          .format(min_fragment_size, max_fragment_size)))

                while fragment_size < min_fragment_size or fragment_size > max_fragment_size:
                    fragment_size = int(input(
                        'You have entered  a bad fragment size, please make sure to enter a value bigger than {} and less than {} :'
                            .format(min_fragment_size, max_fragment_size)))

                if menu == '1':
                    enable_keep_alive = 0
                    print("Sending Text ......")
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
                                    print('The Fragment {} has been received with unexpected state'.format(seq))
                        if (seq - 1) == numberOfNeededFragments:
                            print("The text has been received successfully")
                        else:
                            print("The text has been received with errors")
                    enable_keep_alive = 1
                elif menu == '2':
                    enable_keep_alive = 0
                    enable_simulation = input("Would you like to simulate of file transfer error, (Y)es, (N)o ")
                    if enable_simulation == "Y":
                        print("some random data would be inserted instead of a real packet")
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

                                #fix the error and resend it
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
                        start_exec = time.time()
                        fileNameWithContent = bytearray()
                        fileNameWithContent.extend(fileName.encode())
                        fileNameWithContent.extend(fileContent)
                        while seq <= numberOfNeededFragments:
                            start = (seq - 1) * fragment_size
                            end = seq * fragment_size
                            fragment = fileNameWithContent[start:end]
                            crcValue = binascii.crc_hqx(fragment, 0)
                            head = header.pack(2, current_fileTypeCode, seq, numberOfNeededFragments, len(fragment),
                                               crcValue)
                            packet = b"".join([head, fragment])
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
                                    print('The Fragment {} has been received with unexpected state'.format(seq))
                        if (seq - 1) == numberOfNeededFragments:
                            print("The text has been received successfully")
                        else:
                            print("The text has been received with errors")
                    enable_keep_alive = 1
                else:
                    continue


def receiver():
    print('Mode is Receiver ...')
    global host, port, seq, fragment_size, headerSize, fullText, currentFileExtention, serverBuffer

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
                                # fullText += fragmentToBeReceived.decode()
                                crc_for_received_fragment = binascii.crc_hqx(fragmentToBeReceived, 0)

                        if seq < numberOfexpectedFragments:
                            print("The text is being downloaded")
                        elif seq == numberOfexpectedFragments:
                            print("The text has been received successfully {}".format(fullText))
                            fullText = ""
                        else:
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
                                print("Sent Ack state for the fragment {}".format(headerInfo[2]))
                            else:
                                head = header.pack(0, headerInfo[1], headerInfo[2], headerInfo[3], headerInfo[4],
                                                   headerInfo[5])
                                packet = b"".join([head, fragmentToBeReceived])
                                sock.sendto(packet, address_r)
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
                            print("The file has been received successfully")
                            try:
                                f = open(fileNameAtRecevier + currentFileExtention, 'wb')
                                if currentFileExtention == '.pdf' or currentFileExtention == '.jpg' :
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
                            print("Unexpected Behaviour")
                elif headerInfo[0] == 14:
                     keep_alive_pckt = header.pack(14, 1, 0, 0, 0, 0)
                     sock.sendto(keep_alive_pckt,address)

def extractFileInfoFromPdfJpg(buffer):
    foundAtIndex = -1
    for x in range(0, len(buffer), 1):
        if buffer[x:x + 4].decode() == '.pdf' or buffer[x:x + 4].decode() == '.jpg':
            foundAtIndex = x
            break
        else:
            foundAtIndex = -1
    return foundAtIndex

import threading
start = time.time()

def run_keep_alive():
    global enable_keep_alive,sock_t
    while True:
        if enable_keep_alive == 1:
            print(sock_t[0])
            try:
                keep_alive_pckt = header.pack(14, 1, 0, 0, 0, 0)
                sock_t[0].sendto(keep_alive_pckt,sock_t[1])
                print("\n Alive")
                packet, address_r = sock_t[0].recvfrom(1500)
            except:
                print("sock not init")
        time.sleep(3)

def my_inline_function():
    # do some stuff
    download_thread = threading.Thread(target=run_keep_alive, name="keep alive")
    download_thread.start()
    # continue doing stuff
def main():
    global min_fragment_size, max_fragment_size,enable_keep_alive
    print("1- Server")
    print("2- Client")

    my_inline_function()
    while True:

        mode = input("Please choose your mode (1 or 2): ")
        if mode == "1":
            receiver()
            break
        elif mode == "2":
            sender()
            break
        else:
            print("You've entered a bad mode, please choose correctly")


if __name__ == "__main__":
    main()
