import socket as sc
from struct import *

header = Struct('BBHHHH')
headerSize = calcsize('BBIIHI')

host = "127.0.0.1"
port = 55555
seq = 1


def sender(address):
    global seq
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
    else:
        return address_r, sock


def receiver():
    global host, port, seq
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
    return address_r, sock


def main():
    mode = input("Please choose your mode: ")
    if mode == "server":
        receiver()
    elif mode == "client":
        host_l = input('Please enter destination address:  ')
        port_l = input('Please enter destination port:  ')
        address = (host_l, int(port_l))
        sender(address)
    else:
        print("abdo")

    return


if __name__ == "__main__":
    main()
