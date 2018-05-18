#!/usr/bin/python3

from enum import Enum, IntEnum
from threading import Thread
import random
import time

class Tile(Enum):
    Water  = 0
    Island = 1
    Ship   = 2

    @property
    def free(self):
        return self == Tile.Water

class Ship(IntEnum):
    CARRIER    = 5
    BATTLESHIP = 4
    CRUISER    = 3
    DESTROYER  = 2

    @property
    def count(self):
        opts = {Ship.CARRIER:1,
                Ship.BATTLESHIP:2,
                Ship.CRUISER:3,
                Ship.DESTROYER:4}
        return opts[self]

    def __str__(self):
        return self.name

def shiplength(start,end):
    if start[0] == end[0]:#vertical
        top = max(start[1],end[1])
        bot = min(start[1],end[1])
        return top - bot + 1
    if start[1] == end[1]:#horizontal
        left = min(start[0],end[0])
        right = max(start[0],end[0])
        return right - left + 1

class GameEndException(Exception):
    pass

class Board:

    def __init__(self,dims, viz = None, spec = None, own = True):
        self.dims     = dims
        self.board    = [[Tile.Water for i in range(dims[0])] for j in range(dims[1])]
        self.shiplist = []
        self.shiphits = []
        self.viz      = viz
        self.spec     = spec
        self.ownviz   = own

    def onBoard(self, coord):
        return 0 <= coord[0] < self.dims[0] and 0 <= coord[1] < self.dims[1]

    def get(self, coord):
        return self.board[coord[0]][coord[1]]

    def set(self, coord, val):
        self.board[coord[0]][coord[1]] = val

    def placeIsland(self, coord):
        if self.onBoard(coord) and self.get(coord).free:
            self.set(coord,Tile.Island)
            return True
        else:
            return False
            
    def placeShip(self,start,end):
        shiplen = shiplength(start,end)
        if not shiplen in Ship.__members__.values():
            return (False,"NO VALID SHIPS HAVE THAT LENGTH")
        if [shiplength(*ship) for ship in self.shiplist].count(shiplen) >= Ship(shiplen).count:
            return (False,"TOO MANY SHIPS OF THAT LENGTH")

        if self.onBoard(start) and self.onBoard(end):
            if start[0] == end[0]:#vertical
                top = max(start[1],end[1])
                bot = min(start[1],end[1])
                for y in range(bot,top + 1):
                    coord = (start[0],y)
                    if self.get(coord).free:
                        self.set(coord, Tile.Ship)
                    else:
                        return (False,"ALREADY OCCUPIED")
                self.shiplist.append((start,end))
                self.shiphits.append((Ship(shiplen),False,[(False,(start[0],y)) for y in range(bot,top + 1)]))

            elif start[1] == end[1]:#horizontal
                left = min(start[0],end[0])
                right = max(start[0],end[0])
                for x in range(left,right + 1):
                    coord = (x,start[1])
                    if self.get(coord).free:
                        self.set(coord, Tile.Ship)
                    else:
                        return (False,"ALREADY OCCUPIED")
                self.shiplist.append((start,end))
                self.shiphits.append((Ship(shiplen),False,[(False,(x,start[1])) for x in range(left,right + 1)]))
            else:
                return (False,"NOT HORIZONTAL OR VERTICAL")
        else:
            return (False,"NOT ON BOARD")
        return (True,None)

    def shoot(self,coord):
        (hit,sunkship) = self.doHit(coord)
        #print(hit,sunkship)
        return (hit,sunkship)

    def doHit(self, coord):
        # Return a boolean indicating whether the shot was a hit. If the ship is sunk as a result of the 
        # shot, the ship's type is also returned.
        #print(self.shiphits)
        #print(enumerate(self.shiphits))
        for shipix, (shiptype,shipdead,shipcoords) in enumerate(self.shiphits):
            for ix, (hitstat, shipcoord) in enumerate(shipcoords):
                #print(ix,hitstat,shipcoord)
                if coord == shipcoord:#Hit
                    shipcoords[ix] = (True,shipcoord)
                    if not shipdead and all([deadhere for (deadhere, _) in shipcoords]):#Just sunk
                        self.shiphits[shipix] = (shiptype,True,shipcoords)
                        return (True, shiptype)
                    return (True,None)
        return (False,None)

    def gameover(self):
        return all([shipdead for (_,shipdead,_) in self.shiphits])