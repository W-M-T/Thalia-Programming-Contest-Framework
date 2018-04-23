#!/usr/bin/python3

#sudo apt-get install python3-tk
from tkinter import *
from enum import Enum
from threading import Thread

SIZE = 10
TITLE = "Thalia & Cognac Battleships"

def importImg(path, subs):
    return PhotoImage(file = path).subsample(subs)

def coordToGrid(x, y):
    res = (-y + (SIZE - 1), x + 1)
    return res

class Visualiser():
    #TODO Refactor this stuff
    def initTable(self, window, labeltable, show):
        for y in range(SIZE + 1):
            lrow = []
            for x in range(SIZE + 1):
                templabel = None
                if y == SIZE:
                    if x == 0:
                        templabel = Label(window)
                    else:
                        templabel = Label(window, text=str((x-1)))
                elif x == 0:
                    templabel = Label(window, text=str(SIZE - y - 1))
                else:
                    templabel = Label(window, image=self.WATER if show else self.QUESTIONMARK)

                templabel.configure(background = "#FFFFFF")
                templabel.grid(row=y, column=x)
                lrow.append(templabel)
            labeltable.append(lrow)

    def resetBoth(self):
        for own in range(0,2):
            root = self.own if own == 1 else self.other
            table = self.own_labeltable if own == 1 else self.other_labeltable
            show = self.show_own if own == 1 else self.show_other
            
            for y in range(SIZE):
                for x in range(SIZE):
                    gridcoord = coordToGrid(x,y)
                    table[gridcoord[0]][gridcoord[1]].configure(image=self.WATER if show else self.QUESTIONMARK)
            root.update()

    def updateTitle(self,own_name,other_name):
        self.own.wm_title(TITLE + " - " + own_name)
        self.own.update()
        self.other.wm_title(TITLE + " - " + other_name)
        self.other.update()


    def __init__(self, subs, show_own, show_other):
        self.own = Tk()
        self.own.wm_title(TITLE + " - You")
        self.own.config(background = "#FFFFFF", padx=10, pady=10)

        self.other = Toplevel()
        self.other.wm_title(TITLE + " - Other")
        self.other.config(background = "#FFFFFF", padx=10, pady=10)

        #https://github.com/twitter/twemoji
        self.WATER          = importImg('img/80x80/wave.png', subs)
        self.ISLAND         = importImg('img/80x80/mountain.png', subs)
        self.BOOM           = importImg('img/80x80/boom.png', subs)
        self.SHIP_HIT_TOP   = importImg('img/80x80/red_uparrow.png', subs)
        self.SHIP_HIT_BOT   = importImg('img/80x80/red_downarrow.png', subs)
        self.SHIP_HIT_MID   = importImg('img/80x80/red_square.png', subs)
        self.SHIP_HIT_LEFT  = importImg('img/80x80/red_leftarrow.png', subs)
        self.SHIP_HIT_RIGHT = importImg('img/80x80/red_rightarrow.png', subs)
        self.SHIP_TOP       = importImg('img/80x80/uparrow.png', subs)
        self.SHIP_BOT       = importImg('img/80x80/downarrow.png', subs)
        self.SHIP_MID       = importImg('img/80x80/square.png', subs)
        self.SHIP_LEFT      = importImg('img/80x80/leftarrow.png', subs)
        self.SHIP_RIGHT     = importImg('img/80x80/rightarrow.png', subs)
        self.CROSS          = importImg('img/80x80/cross.png', subs)
        self.QUESTIONMARK   = importImg('img/80x80/questionmark.png', subs)
        self.TROPHY         = importImg('img/160x160/trophy.png', subs)
        self.SKULL          = importImg('img/160x160/skull.png', subs)

        self.own_labeltable   = []
        self.show_own = show_own
        self.initTable(self.own, self.own_labeltable, show_own)
        self.other_labeltable = []
        self.show_other = show_other
        self.initTable(self.other, self.other_labeltable, show_other)

        self.own.resizable(0,0)
        self.own.update()
        self.other.resizable(0,0)
        self.other.update()


    def placeShip(self, own, start, end):
        root = self.own if own else self.other
        table = self.own_labeltable if own else self.other_labeltable
        
        if start[0] == end[0]: #x coord doesn't change, i.e. up-down
            top = (start[0],max(start[1],end[1]))
            bot = (start[0],min(start[1],end[1]))

            gridcoord = coordToGrid(*top)
            table[gridcoord[0]][gridcoord[1]].configure(image=self.SHIP_TOP)
            gridcoord = coordToGrid(*bot)
            table[gridcoord[0]][gridcoord[1]].configure(image=self.SHIP_BOT)
            for i in range(bot[1] + 1, top[1]):
                gridcoord = coordToGrid(start[0], i)
                table[gridcoord[0]][gridcoord[1]].configure(image=self.SHIP_MID)
        elif start[1] == end[1]: #horizontal
            left = (min(start[0],end[0]),start[1])
            right = (max(start[0],end[0]),start[1])

            gridcoord = coordToGrid(*left)
            table[gridcoord[0]][gridcoord[1]].configure(image=self.SHIP_LEFT)
            gridcoord = coordToGrid(*right)
            table[gridcoord[0]][gridcoord[1]].configure(image=self.SHIP_RIGHT)
            for i in range(left[0] + 1, right[0]):
                    gridcoord = coordToGrid(i, start[1])
                    table[gridcoord[0]][gridcoord[1]].configure(image=self.SHIP_MID)
        root.update()

    def change(self, own, coord, img):
        root = self.own if own else self.other
        table = self.own_labeltable if own else self.other_labeltable
        gridcoord = coordToGrid(*coord)
        table[gridcoord[0]][gridcoord[1]].configure(image=img)
        root.update()

    def showResult(self, own, img):#unfinished
        #use two frames (one with result, one with grid)
        root = self.own if own else self.other
        table = self.own_labeltable if own else self.other_labeltable
        gridcoord = coordToGrid(3,4)
        skull = Label(root, image=self.TROPHY)
        skull.configure(background = "#FFFFFF")
        skull.grid(column=gridcoord[0],row=gridcoord[1],rowspan=2,columnspan=2)
        root.update()


if __name__ == "__main__":
    v = Visualiser(1,True,False)
    v.placeShip(True,(1,1),(1,5))
    v.placeShip(False,(2,2),(4,2))
    v.change(True,(3,3),v.ISLAND)
    #v.showResult(True,None)

    import time
    time.sleep(5)
    v.resetBoth()
    time.sleep(90)