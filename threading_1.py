import threading
import time


def worker():
    counter = 0
    while True:
        time.sleep(1)
        counter += 1
        return counter


def print_counter(counter: int):
    print(f"Counter: {counter}")


t1 = threading.Thread(target=worker)

