import time
from SpaceAPIClient import client

BASE='http://localhost:5000'
INTERVAL=1
c=client(base=BASE)

def door_monitor(interval=1):
    doorclosed = c.doorClosedState()
    while True:
        try:
            new_doorclosed = c.doorClosedState()
            if  new_doorclosed != doorclosed:
                doorclosed = new_doorclosed
                print("Door %s"%("Closed" if doorclosed else "Opened"))
            time.sleep(interval)
        except KeyboardInterrupt:
            print("Quitting Safely")
            break

if __name__ == '__main__':
    door_monitor(INTERVAL)

