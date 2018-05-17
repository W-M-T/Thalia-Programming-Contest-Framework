#!/usr/bin/python3

from Bot import *


class ExampleBot(Bot):
    def __init__(self):
        super().__init__()
        self.turnDelay = 0.1
        self.placementIndex = 0  
        #placementIndex is used to choose an island and shot location. You may remove it if you do not use it.

    def choose_ship_location(self):
        # This example function only places all ships horizontally,
        # each above the other, starting in the bottom left corner.
        # You should write a better method.
        
        shipSize = self.choose_ship_size()-1
        #Choose the ship's left position
        x1 = 1
        y1 = -1
        for y in range(self.ownBoard.dims[1]):
            if self.ownBoard.get((x1,y)).free:
                y1 = y
        if y1 == -1:
            raise Exception("Could not place ship along left border.")

        x2 = x1+shipSize
        y2 = y1
        return ((x1,y1), (x2,y2))

    def choose_island_location(self):
        # This is a dummy method, you should write a better one.
        self.placementIndex += 1
        return (int(self.placementIndex/10),self.placementIndex%10)

    def choose_shot_location(self):
        # This is a dummy method, you should write a better one.
        self.placementIndex += 1
        return (int(self.placementIndex/10),self.placementIndex%10)

    def choose_ship_size(self):
        return super().choose_ship_size()
        # You may want to extend this method, but it is not required.

    def handle_result(self,text):
        super().handle_result(text)
        # You may want to extend this method, but it is not required.

    def handle_update(self,text):        
        super().handle_update(text)
        # You may want to extend this method, but it is not required.


if __name__ == "__main__":
    ExampleBot().run()