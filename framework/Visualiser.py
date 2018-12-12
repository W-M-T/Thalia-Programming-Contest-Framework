#!/usr/bin/python3

import sys, time
import contextlib
with contextlib.redirect_stdout(None):
    import pygame

from enum import Enum
from threading import Thread
from queue import Queue
import math

#Text 20 and TD 60 for projection
#Text 15 and TD 40 for testing


SIZE = 15
TITLE = "Thalia Bomberman"


USE_GIF = True

TEXT_HEIGHT = 15
SCREEN_MARGIN = 5

TD_MARGIN = 1
TD_SIZE = (40,)*2
FIELD_MARGIN = 5
FIELD_RECT = pygame.Rect((FIELD_MARGIN,FIELD_MARGIN), (SIZE*TD_SIZE[0] + (SIZE-1)*TD_MARGIN,SIZE*TD_SIZE[1] + (SIZE-1)*TD_MARGIN))

#TEXT_HEIGHT, TD_SIZE = 20, (60,)*2

def importImg(path):
    temp = pygame.image.load(path)
    return pygame.transform.smoothscale(temp, TD_SIZE)

def makeImgTable(dict):
    #Dict of NAME:filepath
    temp = {}
    for k, v in dict.items():
        temp[k] = importImg(v).convert_alpha()
    return temp

def makeAvatarTable(font, dict):#Should be refactored out, but keep it for now
    #Dict of NAME:filepath
    dims = getInfoDims(font)
    temp = {}
    for k, v in dict.items():
        img = pygame.image.load(v)
        temp[k] = pygame.transform.smoothscale(img, (dims[1],)*2).convert_alpha()
    return temp


def coordToGrid(x, y):
    res = (-y + (SIZE - 1), x + 1)
    return res


def getFieldDims():
    return ((SIZE)*TD_MARGIN + (SIZE)*TD_SIZE[0] + FIELD_MARGIN*2,
        (SIZE)*TD_MARGIN + (SIZE)*TD_SIZE[1] + FIELD_MARGIN*2)

def getFieldIndent(font):
    coordTextSize = font.size(str(SIZE-1))
    return (SCREEN_MARGIN + coordTextSize[0], SCREEN_MARGIN + coordTextSize[1])

def getIndentedFieldDims(font):
    return tuple(map(sum,zip(getFieldDims(),getFieldIndent(font))))

def getInfoDims(font):
    screenwidth = getFieldDims()[0]+getFieldIndent(font)[0]
    ysize = max(TD_SIZE[1],TEXT_HEIGHT*2+FIELD_MARGIN*2)
    return (screenwidth,ysize)

def getScreenDims(font):
    (fieldx,fieldy) = tuple(map(sum,zip(getFieldDims(),getFieldIndent(font))))
    return (fieldx, fieldy + getInfoDims(font)[1])

def coordToSurfacePos(coord):
        return (TD_SIZE[0] + FIELD_MARGIN + (coord[0]-1)*(TD_MARGIN+TD_SIZE[0]), TD_SIZE[1] + FIELD_MARGIN + (coord[1]-1)*(TD_MARGIN+TD_SIZE[1]))

#TODO Add easy way to create thread to run "doUIThread"
class Visualiser():
   
    def initTable(self):
        for y in range(SIZE):
            lrow = []
            for x in range(SIZE):
                if y == 0 or y == SIZE - 1 or x == 0 or x == SIZE - 1:
                    templabel = self.img['WATER']
                else:
                    templabel = self.img['DOT2']

                lrow.append(templabel)
            self.drawTable.append(lrow)

    def initTableAlt(self):
        for y in range(SIZE):
            lrow = []
            for x in range(SIZE):
                templabel = None
                if y == 0 or y == SIZE - 1 or x == 0 or x == SIZE - 1:
                    templabel = self.img['WATER']
                elif x % 2 == 1 and y % 2 == 1:
                    templabel = self.img['MOUNTAIN']
                elif x == 6 and y == 6:
                    templabel = self.img['BOMB']
                elif x == 6 and y == 7:
                    templabel = self.img['BOMB2']
                elif x == 6 and y == 8:
                    templabel = self.img['FIRECRACKER']
                elif x % 2 == 0 and y % 2 == 1 or x % 2 == 1 and y % 2 == 0:
                    templabel = self.img['TREE']
                else:
                    templabel = self.img['DOT2'] #Label(window, image=self.WATER if show else self.QUESTIONMARK)

                lrow.append(templabel)
            self.drawTable.append(lrow)

    def initTableAlt2(self):
        for y in range(SIZE):
            lrow = []
            for x in range(SIZE):
                templabel = None
                if y == 0 or y == SIZE - 1 or x == 0 or x == SIZE - 1:
                    templabel = self.img['WATER']
                elif x % 2 == 0 and y % 2 == 0:
                    templabel = self.img['MOUNTAIN']
                elif x % 2 == 1 and y % 2 == 0 or x % 2 == 0 and y % 2 == 1:
                    templabel = self.img['TREE']
                else:
                    templabel = self.img['DOT2'] #Label(window, image=self.WATER if show else self.QUESTIONMARK)

                lrow.append(templabel)
            self.drawTable.append(lrow)
        self.drawTable[2][1] = self.img['DOT2']
        self.drawTable[1][2] = self.img['DOT2']
        self.drawTable[12][1] = self.img['DOT2']
        self.drawTable[13][2] = self.img['DOT2']
        self.drawTable[12][13] = self.img['DOT2']
        self.drawTable[13][12] = self.img['DOT2']
        self.drawTable[1][12] = self.img['DOT2']
        self.drawTable[2][13] = self.img['DOT2']
        self.drawTable[5][5] = self.img['SHIELD']
        self.drawTable[9][5] = self.img['SHIELD']
        self.drawTable[5][9] = self.img['SHIELD']
        self.drawTable[9][9] = self.img['SHIELD']

    def resetField(self):   
        self.drawTable = []
        self.initTable()


    def __init__(self, is_main, scaling):
        global USE_GIF

        #Maybe put this is some other function?
        pygame.display.init()
        pygame.font.init()
        pygame.mixer.init()
        pygame.mixer.quit()

        self.is_main = is_main

        self.updateQueue = Queue()
        
        pygame.display.set_caption(TITLE)
        pygame.display.set_icon(pygame.image.load("img/fire_1f525.png"))

        #self.font = pygame.font.SysFont([], TEXT_HEIGHT)
        self.font = pygame.font.Font(pygame.font.get_default_font(), TEXT_HEIGHT)
        self.screen = pygame.display.set_mode(getScreenDims(self.font))

        pygame.display.update()
        self.screen.fill(pygame.Color("#FFFFFF"))
        pygame.display.flip()
        #self.own.config(background = "#FFFFFF", padx=10, pady=10)

        #https://github.com/twitter/twemoji
        images = {k : "img/" + v for k,v in {
            'BOMB'          : 'bomb2_1f4a3.png',
            'BOMB2'         : 'bomb_1f4a3.png',
            'BLOWUP'        : 'abouttoblow.png',
            'FIRECRACKER'   : 'firecracker_1f9e8.png',
            'DOT'           : 'white-small-square_25ab.png',
            'DOT2'          : 'white-medium-small-square_25fd.png',
            'DOT3'          : 'white-medium-square_25fb2.png',
            'BLOCK'         : 'black-square-button_1f532.png',
            'SPROUT'        : 'seedling_1f331.png',
            'FIRE'          : 'fire_1f525.png',
            'WATER'         : 'water-wave_1f30a.png',
            'MOUNTAIN'      : 'mountain_26f0.png',
            'CHAR1'         : 'playerblue.png',
            'CHAR2'         : 'playerred.png',
            'CHAR3'         : 'playergreen.png',
            'CHAR4'         : 'playeryellow.png',
            'TREE'          : 'deciduous-tree_1f333.png',
            'TREE1'         : 'seedling_1f331.png',
            'TREE2'         : 'palm-tree_1f334.png',
            'SHIELD'        : 'shield_1f6e1.png',
            'BURNTREE'      : 'burningtree.png',
            'SKULL'         : 'skull-and-crossbones_2620.png'
            }.items()}
        self.img = makeImgTable(images)

        self.avatars = makeAvatarTable(self.font, {k : "img/" + v for k,v in {
            'CHAR1'         : 'playerblue.png',
            'CHAR2'         : 'playerred.png',
            'CHAR3'         : 'playergreen.png',
            'CHAR4'         : 'playeryellow.png',
            'DOT3'          : 'white-medium-square_25fb2.png',
            'SKULL'         : 'skull-and-crossbones_2620.png',
            'HEART'         : 'black-heart-suit_2665.png',
            'FIRE'          : 'fire_1f525.png'
            }.items()}) # TODO import the avatars hi-res


        self.drawFloats = {}
        self.drawBombs = []


        self.playerInfo = [("",-1,False)]*4 # (name, lives, fire)

        
        self.drawTable  = []
        self.fieldLabelSurface = pygame.Surface(getIndentedFieldDims(self.font))
        self.fieldSurface = pygame.Surface(getFieldDims())
        self.infoBoxSurface = pygame.Surface(getInfoDims(self.font))

        self.initTable()

        self.drawScreen()

        

        #self.own.resizable(0,0)

    def drawScreen(self):
        self.screen.fill(pygame.Color("#FFFFFF"))
        self.drawField()

        self.fieldLabelSurface.fill(pygame.Color("#FFFFFF"))
        self.fieldLabelSurface.blit(self.fieldSurface,getFieldIndent(self.font))
        self.drawLabels()

        self.screen.blit(self.fieldLabelSurface,(0,getInfoDims(self.font)[1]))

        self.infoBoxSurface.fill(pygame.Color("#E6E7E8"))
        self.drawInfoBox()

        self.screen.blit(self.infoBoxSurface,(0,0))


        pygame.display.flip()


    def labelMidCoordX(self, n):
        indent = getFieldIndent(self.font)
        yMid = (indent[1] - SCREEN_MARGIN)/2 + SCREEN_MARGIN
        xFieldPos = indent[0] + coordToSurfacePos((n,0))[0] + TD_SIZE[0]/2
        return (xFieldPos, yMid)


    def labelMidCoordY(self, n):
        indent = getFieldIndent(self.font)
        xMid = indent[1]
        yFieldPos = indent[1] + coordToSurfacePos((0,n))[1] + (TD_SIZE[1]+TD_MARGIN)/2
        return (xMid, yFieldPos)

    def drawInfoBox(self):
        dims = getInfoDims(self.font)
        textdims = (dims[1]-SCREEN_MARGIN*2)//2
        singlewidth = dims[0]//4
        inset = 0.8
        iconMake = lambda res: pygame.transform.smoothscale(self.avatars[res], ((round(dims[1]*inset),)*2))#Don't redo this every render
        icons = {k:iconMake(k) for k in ["CHAR1","CHAR2","CHAR3","CHAR4","SKULL","FIRE"]}
        heart = pygame.transform.smoothscale(self.avatars['HEART'], (textdims,)*2)

        for i in range(0,4):
            if self.playerInfo[i][1] > -1:
                tempSurface = pygame.Surface((singlewidth,dims[1]))
                tempSurface.fill(pygame.Color("#E6E7E8"))
                tempSurface.blit(self.avatars['DOT3'],(0,0))
                tempSurface.blit(icons["CHAR{}".format(i+1)] if self.playerInfo[i][1] > 0 else icons["SKULL"], ((round(dims[1]*(1-inset)/2),)*2))

                if self.playerInfo[i][2]:
                    tempSurface.blit(icons["FIRE"], ((round(dims[1]*(1-inset)/2),)*2))
                
                pname = self.font.render("{}".format(self.playerInfo[i][0]), True, (10,10,10))
                tempSurface.blit(pname, (dims[1],SCREEN_MARGIN))
                #tempSurface.blit(pname, (dims[1],SCREEN_MARGIN*2+textdims))
                for j in range(0,self.playerInfo[i][1]):
                    tempSurface.blit(heart, (dims[1]+j*textdims,SCREEN_MARGIN+textdims))

                self.infoBoxSurface.blit(tempSurface, (i*singlewidth, 0))

    def drawLabels(self):
        for i in range(SIZE):
            label = self.font.render(str(i), True, (10,)*3)
            labelmid = (label.get_rect().center[0],self.font.get_height()/2)

            xAxis = self.labelMidCoordX(i)
            xAxPos = (xAxis[0] - labelmid[0], xAxis[1] - labelmid[1]*0.5)
            self.fieldLabelSurface.blit(label, xAxPos)
            yAxis = self.labelMidCoordY(i)
            yAxPos = (yAxis[0] - labelmid[0]*2, yAxis[1] - labelmid[1])
            self.fieldLabelSurface.blit(label, yAxPos)
            #print(yAxPos)
            #pygame.draw.circle(self.screen, (255,0,0), (int(xAxis[0]),int(xAxis[1])), 2, 2)
            #pygame.draw.circle(self.screen, (255,0,0), (int(yAxis[0]),int(yAxis[1])), 2, 2)


    def drawField(self):
        self.fieldSurface.fill(pygame.Color("#FFFFFF"))

        for y, col in enumerate(self.drawTable):
            for x, val in enumerate(col):
                if val is not None:
                    self.fieldSurface.blit(val, coordToSurfacePos((x,y)))

        for (primed, coord) in self.drawBombs:
            self.fieldSurface.blit(self.img['BOMB'] if not primed else self.img['BLOWUP'], coordToSurfacePos(coord))


        for key, agent in self.drawFloats.items():
            image = agent[0]
            coord = agent[1]
            self.fieldSurface.blit(image, coordToSurfacePos(coord))

    def setPlayerInfo(self, pID, info):
        self.playerInfo[pID] = info

    def getPlayerInfo(self, pID):
        return self.playerInfo[pID]

    def addFloat(self, name, coord, img):
        self.drawFloats[name] = (img, coord)

    def addFloatByKey(self, name, coord, key):#Maybe just add a getter method for img?
        if key in self.img:
            self.drawFloats[name] = (self.img[key], coord)

    def addBomb(self, coord):
        self.drawBombs.append((False, coord))

    def primeBomb(self, coord):
        self.drawBombs = list(map(lambda bomb: (True, bomb[1]) if bomb[1] == coord else bomb, self.drawBombs))

    def removeBomb(self, coord):
        self.drawBombs = list(filter(lambda bomb: bomb[1] != coord, self.drawBombs))

    def removeFloat(self, name):
        if name in self.drawFloats:
            del(self.drawFloats[name])

    def change(self, coord, img):
        self.drawTable[coord[1]][coord[0]] = img

    def changeByKey(self, coord, key):
        if key in self.img:
            self.drawTable[coord[1]][coord[0]] = self.img[key]

    def animateWaterIn(self,inset):
        image = self.img['WATER']
        start = inset
        end = SIZE-1 - inset
        rang = range(start,end)
        amount = len(rang)
        for i in range(end - start):
            self.drawTable[start][start + i] = image
            self.drawTable[start][end - i] = image

            self.drawTable[end][start + i] = image
            self.drawTable[end][end - i] = image

            self.drawTable[start + i][start] = image
            self.drawTable[end - i][start] = image

            self.drawTable[start + i][end] = image
            self.drawTable[end - i][end] = image
            self.drawScreen()
            pygame.time.wait(math.ceil(1/(amount-1)*1000))

    def animateWalk(self, agentcoords):
        fps = 60
        sec = 0.5
        steps = math.ceil(sec*fps)

        clock = pygame.time.Clock()

        agentsteps = {}

        for agentname, newpos in agentcoords.items():

            agent = self.drawFloats[agentname]
            startX = agent[1][0]
            startY = agent[1][1]
            deltaX = newpos[0] - startX
            deltaY = newpos[1] - startY

            stepX = deltaX / steps
            stepY = deltaY / steps
            agentsteps[agentname] = (stepX, stepY)

        #TODO doe dit door een mult van step tov start ipv herhaalde additie
        for i in range(steps):
            self.drawScreen()

            for agentname in agentcoords:
                cur = self.drawFloats[agentname]
                curPos = cur[1]
                self.drawFloats[agentname] = (cur[0], (curPos[0] + agentsteps[agentname][0], curPos[1] + agentsteps[agentname][1]))

            clock.tick(fps)

        #finalize to whole number
        for agentname, newpos in agentcoords.items():
            #print(agentname, newpos)
            self.drawFloats[agentname] = (self.drawFloats[agentname][0], newpos)
        self.drawScreen()


    def doUIThread(self):
        while True:
            (func,args) = self.updateQueue.get()
            func(self,*args)

    def syncUpdate(self,func,*args):
        if not self.is_main:
            print("Put in queue")
            self.updateQueue.put((func,args))
        else:
            #print("Doing",func,args)
            func(self,*args)


class VisualiserWrapper:

    def __init__(self, viz):
        self.viz = viz

    def syncUpdate(self,func,*args):
        #print(func)
        if self.viz is not None:
            self.viz.syncUpdate(func,*args)



if __name__ == "__main__":
    v = Visualiser(True,1)
    #v.change((3,3),v.img['ISLAND'])
    #v.showResult(True,None)

    v.addFloat('p1', (6,5), v.img['CHAR1'],)
    v.setPlayerInfo(0,("Teamname",3,False))
    v.addFloat('p2', (6,10), v.img['CHAR2'])
    v.setPlayerInfo(1,("Teamname",3,False))
    v.addFloat('p3', (6,9), v.img['CHAR3'])
    v.setPlayerInfo(2,("Teamname",3,False))
    v.drawScreen()
    

    import time
    time.sleep(2)
    
    v.animateWalk({'p1':(6,4),'p2':(7,10)})
    v.setPlayerInfo(2,("Teamname",2,False))
    v.animateWalk({'p1':(7,4),'p2':(8,10)})
    v.setPlayerInfo(2,("Teamname",1,False))
    v.animateWalk({'p1':(7,5),'p2':(8,9)})
    v.setPlayerInfo(2,("Teamname",0,True))
    v.animateWalk({'p1':(8,5),'p2':(8,8)})
    v.setPlayerInfo(2,("Teamname",-1,False))
    
    time.sleep(2)
    
    
    for i in range(4):
        v.animateWaterIn(i+1)
        #v.animateWaterIn(i,None)
    
    time.sleep(65)