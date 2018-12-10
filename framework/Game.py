#!/usr/bin/env python3

from enum import Enum
from threading import Thread
import random
import time
from .Util import lbRecv, sockSend

from .Visualiser import Visualiser

TURNTIMEOUT      = 2.0
MINTURNTIME      = 0.5

class Tile(Enum):
    Water       = 0
    Mountain    = 1
    Tree        = 2
    Empty       = 3

    @property
    def unbreakable(self):
        return self == Tile.Water or self == Tile.Mountain
    


class GameEndException(Exception):
    pass

class Board:

    def __init__(self,dims):
        self.dims    = dims
        self.board   = [[Tile.Empty for i in range(dims[0])] for j in range(dims[1])]
        self.bombs   = []#Lijst van dicts met pos en timer
        self.players = {}#dict van names naar pos en lives

    def fillBoard1(self):
        for y in range(self.dims[1]):
            for x in range(self.dims[0]):
                if y == 0 or y == self.dims[1] - 1 or x == 0 or x == self.dims[0] - 1:
                    self.board[x][y] = Tile.Water
                elif x % 2 == 0 and y % 2 == 0:
                    self.board[x][y] = Tile.Mountain
                elif x % 2 == 1 and y % 2 == 0 or x % 2 == 0 and y % 2 == 1:
                    self.board[x][y] = Tile.Tree

        self.board[2][1] = Tile.Empty
        self.board[1][2] = Tile.Empty
        self.board[self.dims[0]-3][1] = Tile.Empty
        self.board[self.dims[0]-2][2] = Tile.Empty
        self.board[self.dims[0]-3][self.dims[1]-2] = Tile.Empty
        self.board[self.dims[0]-2][self.dims[1]-3] = Tile.Empty
        self.board[1][self.dims[1]-3] = Tile.Empty
        self.board[2][self.dims[1]-2] = Tile.Empty

    def placePlayers(self, playercount):
        self.players["p1"]      = {"lives": 2, "pos": (1,1)}
        self.players["p2"]      = {"lives": 2, "pos": (self.dims[0]-2,self.dims[1]-2)}
        if playercount >= 3:
            self.players["p3"]  = {"lives": 2, "pos": (self.dims[0]-2,1)}
        if playercount == 4:
            self.players["p4"]  = {"lives": 2, "pos": (1,self.dims[1]-2)}

    def onBoard(self, coord):
        return 0 <= coord[0] < self.dims[0] and 0 <= coord[1] < self.dims[1]

    def get(self, coord):
        return self.board[coord[0]][coord[1]]

    def set(self, coord, val):
        self.board[coord[0]][coord[1]] = val

    def is_valid_move(self, coord):
        return self.get(coord) == Tile.Empty

    def gameover(self):
        pass

    def livePlayerCount(self):
        return len(list(filter(lambda x: x is not None, self.players)))


def writeTo(client,data):
    try:
        #print("@{}\t".format(client["name"]),end="")
        #print(data)
        sockSend(client["socket"],data)
        return True
    except Exception as e:
        print(e.__class__.__name__, e)
        return False

def informSpectator(spec, text):
    #print("spectator is",spec)
    try:
        if spec is "None":
            print("!!!None string found!!!")
        if spec is not None and not spec == "None":#Ugly hack
            sockSend(spec, text)
    except Exception as e:
        pass

class connClosedException(Exception):
    pass

def readFrom(client):
    return lbRecv(client["socket"], client["linebuffer"])




class GameRunner(Thread):  
    #implement timeouts

    #combineer socket en linebuffer in een object?
    #teamname, socket, addr
    def __init__(self, clients, viz = None, spectator = None):
        super(GameRunner, self).__init__()

        self.clients = clients
        self.viz = viz
        self.spectator = spectator

        for client in self.clients:
            client["linebuffer"] = []
            #client["socket"].settimeout(None)

        self.BOARDSIZE = (15,)*2
        self.board = Board(self.BOARDSIZE)
        self.board.fillBoard1()
        self.board.placePlayers(len(clients))
        if viz is not None:
            self.updateMapViz()
            self.setPlayersViz()

        self.end  = False

        self.waterlevel = 0
        
            

    def disqualify(self, client, reason):
        '''
        writeTo(self.turnClient(),"GAME RESULT YOU LOST (DISQUALIFIED: {})".format(reason))
        writeTo(self.otherClient(), "GAME RESULT YOU WON")
        '''

        raise GameEndException("{} was disqualified!! Reason: {}".format("someone", reason))


    def waitReady(self):
        ready = []
        for client in self.clients:
            ready.append(readFrom(client).find("READY") == 0)

        if not all(ready):
            raise GameEndException("Never readied up")


    #improve this
    def explode(self, coord):
        self.viz.syncUpdate(Visualiser.change, [coord, self.viz.img['FIRE']])
        self.killCoord(*coord)

        for y in range(coord[1]-1,0,-1):
            if not self.explodeHere(coord[0], y):
                break
        for y in range(coord[1]+1,self.BOARDSIZE[1]):
            if not self.explodeHere(coord[0], y):
                break

        for x in range(coord[0]-1,0,-1):
            if not self.explodeHere(x, coord[1]):
                break
        for x in range(coord[0]+1,self.BOARDSIZE[1]):
            if not self.explodeHere(x, coord[1]):
                break

        self.viz.syncUpdate(Visualiser.drawScreen, [])

    def explodeHere(self, x, y):
        #return False if ended
        #return True if continue
        self.killCoord(x,y)

        if self.board.board[y][x].unbreakable:
            return False
        elif self.board.board[y][x] == Tile.Tree:
            self.board.board[y][x] = Tile.Empty
            self.viz.syncUpdate(Visualiser.change, [(x,y), self.viz.img['BURNTREE']])
            return False
        else:
            self.viz.syncUpdate(Visualiser.change, [(x,y), self.viz.img['FIRE']])
            return True

    def killCoord(self, x, y):
        #TODO FIX THIS (bad)
        foundHere = list(filter((lambda t: self.board.players[t] is not None and self.board.players[t]['pos'] == (x,y)),self.board.players))
        for p in foundHere:
            print("Killing",p)
            self.viz.syncUpdate(Visualiser.addFloat, [p,self.board.players[p]['pos'],self.viz.img['SKULL']])
            self.board.players[p] = None


    def updateMapViz(self):
        if self.viz is not None:#Implementeer dit op een andere wijze (wrappermethode die de is None check doet)
            for y in range(self.BOARDSIZE[1]):
                for x in range(self.BOARDSIZE[0]):
                    self.viz.syncUpdate(Visualiser.change, [(x,y), {
                                            Tile.Water:self.viz.img['WATER'],
                                            Tile.Mountain:self.viz.img['MOUNTAIN'],
                                            Tile.Tree:self.viz.img['TREE'],
                                            Tile.Empty:self.viz.img['DOT2']
                                            }[self.board.board[y][x]]])
            self.viz.syncUpdate(Visualiser.drawScreen, [])
            print("Screen should update now")

    def setPlayersViz(self):
        images = list(map((lambda x: self.viz.img['CHAR{}'.format(x)]), list(range(1,5))))
        print(images)
        random.shuffle(images)

        for ix, (player,info) in enumerate(self.board.players.items()):
            print(player)
            self.viz.syncUpdate(Visualiser.addFloat, [player,info['pos'],images[ix]])
        self.viz.syncUpdate(Visualiser.drawScreen, [])

    def updatePlayerViz(self):
        moves = {}
        for player, info in self.board.players.items():
            if info is not None:
                moves[player] = info['pos']
        self.viz.syncUpdate(Visualiser.animateWalk, [moves])

    def clearFires(self):
        for y in range(self.BOARDSIZE[1]):
            for x in range(self.BOARDSIZE[0]):
                if self.board.board[y][x] == Tile.Empty:
                    self.viz.syncUpdate(Visualiser.change, [(x,y), self.viz.img['DOT2']])
        for p, info in self.board.players.items():
            if info == None:
                self.viz.syncUpdate(Visualiser.removeFloat, [p])

    def doWater(self):
        self.clearFires()
        self.waterlevel += 1
        for y in range(self.BOARDSIZE[1]):
            self.killCoord(self.waterlevel, y)
            self.board.board[y][self.waterlevel] = Tile.Water
            self.killCoord(self.BOARDSIZE[0] - 1 - self.waterlevel, y)
            self.board.board[y][self.BOARDSIZE[0] - 1 - self.waterlevel] = Tile.Water

        for x in range(self.BOARDSIZE[0]):
            self.killCoord(x, self.waterlevel)
            self.board.board[self.waterlevel][x] = Tile.Water
            self.killCoord(x, self.BOARDSIZE[1] - 1 - self.waterlevel)
            self.board.board[self.BOARDSIZE[0] - 1 - self.waterlevel][x] = Tile.Water
        self.viz.animateWaterIn(self.waterlevel, self.viz.img['WATER'])


    def doAct(self):
        #Clear fire, trees and skulls
        self.clearFires()

        #Perform actions
        for player, info in self.board.players.items():
            if info is not None:
                (x,y) = self.board.players[player]['pos']
                choices = ([(1,0)] if x != 13 else []) + ([(0,1)] if y != 13 else []) + ([(-1,0)] if x != 1 else []) + ([(0,-1)] if y != 1 else [])
                choices = list(filter((lambda coord: self.board.board[y+coord[1]][x+coord[0]] == Tile.Empty), choices))
                (dx, dy) = random.choice(choices)
                self.board.players[player]['pos'] = (x + dx, y + dy)
        self.updatePlayerViz()

    def primeBombs(self):
        for bomb in self.board.bombs:
            if bomb['timer'] == 1:
                #self.viz.syncUpdate(Visualiser.addFloat, [bomb, bomb['pos'], self.viz.img['BLOWUP']])
                pass

    def doBlow(self):
        self.primeBombs()
        self.explode((1, 1))

    def doTurn(self):
        self.doAct()
        #time.sleep(1)
        self.doBlow()
        time.sleep(0.3)

    def run(self):
        try:
            print(" versus ".join(map(lambda x: x['name'], self.clients)))

            #informSpectator(self.spectator,"updateTitle True {}".format(self.clientA["name"]))
            #if self.viz is not None:
            #    self.viz.syncUpdate(Visualiser.updateTitle, [self.clientA["name"],self.clientB["name"]])

            #combinations(self.clients, len(self.clients) - 1)
            for client in self.clients:
                writeTo(client,"CHALLENGED BY {}".format("a bunch of others"))
            #writeTo(self.clientA,"CHALLENGED BY {}".format(self.clientB["name"]))
            #writeTo(self.clientB,"CHALLENGED BY {}".format(self.clientA["name"]))

            #self.waitReady()
            self.board.bombs.append({'pos':(7,7),'timer':1})
            for i in range(5):
                self.doTurn()
            
            
        except (GameEndException,connClosedException) as e:
            print(e)

        for client in self.clients:
            #client["socket"].close()
            pass

        informSpectator(self.spectator,"end")

        time.sleep(1)
        #self.board.players['p1']['pos'] = (7,)*2
        #self.updatePlayerViz()
        #time.sleep(5)
        for i in range(4):
            self.doWater()
        #    self.viz.animateWaterIn(i+1,self.viz.img['WATER'])
            #v.animateWaterIn(i,None)
        if self.viz is not None:
            time.sleep(15)
            #self.viz.syncUpdate(Visualiser.resetBoth, [])
            #self.viz.syncUpdate(Visualiser.updateTitle, ["",""])
        

def main():
    viz = Visualiser(True, 1)#None#
    gr = GameRunner([{"name":"testerbot"},{"name":"randbot"},{"name":"silentbot"},{"name":"mutebot"}],viz=viz)
    gr.run()
    


if __name__ == "__main__":
    main()
