#!/usr/bin/python3

import sys
import re
from Game import Board, Ship, Tile
from enum import Enum,IntEnum
import random, time

class ShipSizes(IntEnum):
    Destroyer  = 2
    Cruiser    = 3
    Battleship = 4
    Carrier    = 5

class ShipAmounts(IntEnum):
    Destroyer  = 4
    Cruiser    = 3
    Battleship = 2
    Carrier    = 1

class Bot():
    def __init__(self):
        from Visualiser import Visualiser
        self.ownBoard = Board((10,10),None,own = True)
        self.enemyBoard = Board((10,10),None,own = False)
        self.shipsToPlace = [[size, Ship(size).count] for size in Ship]
        self.turnDelay = 0.1
        self.lastCoord = (0,0)

    def handle_result(self,text):
        if text.find("RESULT HIT") != -1:
            self.enemyBoard.set(self.lastCoord,Tile.Ship)

    def handle_update(self,text):        
        if text.find("RESULT GOTISLAND"):
            tokens = text.strip().split()
            coord = (int(re.sub("\D","",tokens[2])),
                     int(re.sub("\D","",tokens[3])))
            self.ownBoard.set(coord,Tile.Island) 

    def handle_command(self, text):
        tokens = text.strip().split()
        if tokens[0] == 'REQUEST' and tokens[1] == 'ACTION':
            if tokens[2] == 'SHIP':
                location = self.choose_ship_location()
                self.place_ship(location[0], location[1])
            if tokens[2] == 'ISLAND':
                coord = self.choose_island_location()
                self.place_island(coord)
            if tokens[2] == 'SHOT':
                coord = self.choose_shot_location()
                self.shoot(coord)
        if tokens[0] == 'RESULT':
            self.handle_result(text)
        if tokens[0] == 'UPDATE':
            self.handle_update(text)
        if tokens[0] == 'GAME' and tokens[1] == 'RESULT':
            self.done = True



    def choose_ship_location(self):
        raise NotImplementedError("You need to implement your own choose_ship_location method.")

    def choose_ship_size(self):
        #Find a ship size that can still be placed
        shipSize = 0
        for index, (size, count) in enumerate(self.shipsToPlace):
            if count > 0:
                self.shipsToPlace[index][1] -= 1
                return self.shipsToPlace[index][0]
        return shipSize

    def choose_island_location(self):
        self.placementIndex += 1
        return (int(self.placementIndex/10),self.placementIndex%10)

    def choose_shot_location(self):
        self.placementIndex += 1
        return (int(self.placementIndex/10),self.placementIndex%10)


    @staticmethod
    def formatCoord(coord):
        return "(" + str(coord[0]) + "," + str(coord[1]) + ")"

    def place_ship(self, start, end):
        #raise Exception("placeship {0} {1}",start,end)
        success = self.ownBoard.placeShip(start, end)
        if not success[0]:
            pass
            #raise Exception("Illegal ship placement: {0}.",success[1])
        start = "(" + str(start[0]) + "," + str(start[1]) + ")"
        end = "(" + str(end[0]) + "," + str(end[1]) + ")"
        print("PLACE SHIP",start,end)
        sys.stdout.flush()#Nodig?

    def place_island(self, coord):
        success = self.enemyBoard.placeIsland(coord)
        if not success:
            raise Exception("Illegal island placement.")
        coord = Bot.formatCoord(coord)
        print("PLACE ISLAND",coord)

    def shoot(self, coord):
        self.lastCoord = coord
        coord = Bot.formatCoord(coord)
        print("SHOOT", coord)

    def run(self):
        self.done = False
        while self.done != True:
            command = input()
            time.sleep(self.turnDelay)
            self.handle_command(command)


if __name__ == "__main__":
    Bot().run()