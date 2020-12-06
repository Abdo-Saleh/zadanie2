import time

from pynput.keyboard import Key, Listener

start = time.time()

check = int(time.time() - start)
while check <= 3:
    print("i am sending")
    check = int(time.time() - start)
    time.sleep(2)

def on_press(key):
    print("abdo pressed")

def on_release(key):
    print("abdo realeased")


# Collect events until released
with Listener(
        on_press=on_press,
        on_release=on_release) as listener:
    listener.join()


