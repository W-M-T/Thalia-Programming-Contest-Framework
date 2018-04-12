#!/usr/bin/python3

import sys
from enum import Enum,IntEnum
import random


class GamePhase(Enum):
    Ready   = 0
    Islands = 1
    Ships   = 2
    Battle  = 3
    Done    = 4

class ShipSizes(IntEnum):
    Destroyer  = 2
    Cruiser    = 3
    Battleship = 4
    Carrier    = 5 

def handle_command(text):
    tokens = text.strip().split()
    place_ship()

def handle_result(text):
    pass


def place_ship():
    startpos = (0,0)
    endpos = (0,1)
    print("PLACE SHIP",startpos,endpos)
    sys.stdout.flush()#Nodig?

def place_island():
    coord = (0,0)
    print("PLACE ISLAND",coord)

def shoot():
    coord = (0,0)
    print("SHOOT", coord)
    handle_result()
    

def main():
    import time
    time.sleep(1)
    done = False
    while not done:
        command = input()
        handle_command(command)

if __name__ == "__main__":
    main()