#!/usr/bin/python3

import sys
import re
from framework.Game import Board, Tile


class Bot:
    def __init__(self):
        """Initialize instance variables."""
        self.ownBoard = Board((15, 15))
        self.enemyBoard = Board((15, 15))
        self.lastCoord = (0, 0)

    def handle_result(self, text):
        """Handle the server's result message."""
        if text.find("RESULT HIT") != -1:
            self.enemyBoard.set(self.lastCoord, Tile.Ship)

    def handle_update(self, text):
        """Handle the server's update message."""
        if text.find("RESULT GOTISLAND"):
            tokens = text.strip().split()
            coord = (int(re.sub("\D", "", tokens[2])),
                     int(re.sub("\D", "", tokens[3])))
            self.ownBoard.set(coord, Tile.Island)

    def handle_command(self, text):
        """Handle the server's message."""
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
        """Return a location where a ship should be placed."""
        raise NotImplementedError(
            "You need to implement your own choose_ship_location method.")

    def choose_ship_size(self):
        """"Return a ship size that can be placed on the board."""
        shipSize = 0
        for index, (size, count) in enumerate(self.shipsToPlace):
            if count > 0:
                self.shipsToPlace[index][1] -= 1
                return self.shipsToPlace[index][0]
        return shipSize

    def choose_island_location(self):
        """Return the next island's location."""
        self.placementIndex += 1
        return (int(self.placementIndex / 10), self.placementIndex % 10)

    def choose_shot_location(self):
        """Return the next shot's location."""
        self.placementIndex += 1
        return (int(self.placementIndex / 10), self.placementIndex % 10)

    @staticmethod
    def formatCoord(coord):
        """Return a properly formatted coordinate string."""
        return "(" + str(coord[0]) + "," + str(coord[1]) + ")"

    def place_ship(self, start, end):
        """Print a command to stdout with the next ship's desired coordinates."""
        success = self.ownBoard.placeShip(start, end)
        if not success[0]:
            raise Exception("Illegal ship placement: {0}.", success[1])
        start = "(" + str(start[0]) + "," + str(start[1]) + ")"
        end = "(" + str(end[0]) + "," + str(end[1]) + ")"
        print("PLACE SHIP", start, end)
        sys.stdout.flush()  # Nodig?

    def place_island(self, coord):
        """Print a command to stdout with the next island's desired coordinates."""
        success = self.enemyBoard.placeIsland(coord)
        if not success:
            raise Exception("Illegal island placement.")
        coord = Bot.formatCoord(coord)
        print("PLACE ISLAND", coord)

    def shoot(self, coord):
        """Print a command to stdout with the next shot's desired coordinates."""
        self.lastCoord = coord
        coord = Bot.formatCoord(coord)
        print("SHOOT", coord)

    def run(self):
        """Run the bot."""
        self.done = False
        while self.done != True:
            command = input()
            self.handle_command(command)


if __name__ == "__main__":
    Bot().run()
