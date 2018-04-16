#!/usr/bin/python3

from enum import Enum, IntEnum
from threading import *
import random
import time

class Tile(Enum):
    Water = False
    Ship = True

    def __str__(self):
        if self == Tile.Water:
            return "\033[1;34m🌊\033[0;0m"
        else:
            return "🛥"

class Board:

    def __init__(self,dims):
        self.board = [[Tile.Water for i in range(dims[0])] for j in range(dims[1])]

        
        for i in range(10):
            x = random.randint(0,dims[0]-1)
            y = random.randint(0,dims[1]-1)
            self.board[x][y] = Tile.Ship



def writeTo(client,data):
    try:
        client["socket"].send(data.encode("utf-8"))
        return True
    except Exception as e:
        print(e)
        return False

def readFrom(client):
    try:
        response = client["socket"].recv(4096)
    except Exception as e:
        print(e)
        return None

class GameRunner(Thread):  
    #implement timeouts


    #teamname, socket, addr
    def __init__(self, clientA, clientB):
        super(GameRunner, self).__init__()
        self.clientA = clientA
        self.clientB = clientB
        
        self.clientA["socket"].settimeout(None)
        self.clientB["socket"].settimeout(None)

        self.turn      = random.randint(0,1)

    

    def doIslands(self):
        print(self.clientA["name"], "versus", self.clientB["name"])
        pass

    def doShips(self):
        pass

    def doBattle(self):
        pass

    def run(self):
        print(self.clientA["name"], "versus", self.clientB["name"])
        #writeTo(self.clientA,"FUCK OFF")
        print("GAMERUNNER SLEEPY")
        time.sleep(15)
        self.clientA["socket"].close()
        self.clientB["socket"].close()
        print("GAMERUNNER ENDED")
        #self.doIslands()
        #self.doShips()
        #self.doBattle()

def main():
    
    gr = GameRunner({"name":"hi"},{"name":"randombot2"})
    gr.start()

    field = Board((10,10))
    for b in field.board:
        for a in b:
            print(a,end=" ")
        print()

if __name__ == "__main__":
    main()