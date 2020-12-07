import time

switch = False


def sender():
    print("sender")
    while True:
        time.sleep(4)
        switch = True


def reciver():
    print("recevier")
    while True:
        time.sleep(3)


if __name__ == '__main__':
    global switch
print("1- Server")
print("2- Client")
mode = input("Please choose your mode (client or server) (1 or 2): ")
if mode == "1":
    print("1- Sender")
    print("2- Reciver")
    if switch == True:
        sender()
    elif switch == False :
        reciver()
    else:
        print("You've entered a bad mode, please choose correctly")
        # break

elif mode == "2":
    host_l = input('Please enter destination address:  ')
    port_l = input('Please enter destination port:  ')
    sock, address = senderSocket(host_l, port_l)
    sock_t = sock
    value = 0
    sender(sock, address)
    # print("1- Sender")
    # print("2- Reciver")
    # choice = input("Please choose your mode (sender or receiver) (1 or 2): ")
    # if choice == '1':
    #     sender(sock, address)
    # elif choice == '2':
    #     receiver(sock, address)
    # else:
    #     print("You've entered a bad mode, please choose correctly")


else:
    print("You've entered a bad mode, please choose correctly")
