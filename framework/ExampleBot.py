#!/usr/bin/python3


from Bot import *
class ExampleBot(Bot):
    def __init__(self):
        super().__init__()
        self.turnDelay = 0.1
        self.placementIndex = 0

    def handle_result(self,text):
        super().handle_result(text)

    def handle_update(self,text):        
        super().handle_update(text)

    
    def choose_ship_location(self):
        #This example function only places all ships horizontally,
        #each above the other, starting in the bottom left corner.

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
        self.placementIndex += 1
        return (int(self.placementIndex/10),self.placementIndex%10)

    def choose_shot_location(self):
        self.placementIndex += 1
        return (int(self.placementIndex/10),self.placementIndex%10)

    def choose_ship_size(self):
        super().choose_ship_size()

if __name__ == "__main__":
    ExampleBot().run()