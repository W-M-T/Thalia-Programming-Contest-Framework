#!/usr/bin/env python3

from enum import Enum
from threading import Thread
import random
import time
from Util import lbRecv, sockSend, RecvBuffer

from Visualiser import Visualiser, VisualiserWrapper

TURNTIMEOUT      = 2.0
MINTURNTIME      = 0.5

LIVES = 3
WATERROUNDS = [40,60,80,100]


class Tile(Enum):
    Water       = 0
    Mountain    = 1
    Tree        = 2
    Empty       = 3

    @property
    def unbreakable(self):
        return self == Tile.Water or self == Tile.Mountain

class Dir(Enum):
    UP      = (0, -1)
    LEFT    = (-1, 0)
    DOWN    = (0, 1)
    RIGHT   = (1, 0)
    

class GameEndException(Exception):
    pass


class Board:

    def __init__(self,dims):
        self.dims    = dims
        self.board   = [[Tile.Empty for i in range(dims[0])] for j in range(dims[1])]
        self.bombs   = []#Lijst van dicts met pos en timer
        self.players = {}#dict van pids naar pos en lives

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

    def placePlayers(self, playercount, lives):
        pos_options = [
                        (1,1),
                        (self.dims[0]-2,self.dims[1]-2),
                        (self.dims[0]-2,1),
                        (1,self.dims[1]-2)
                        ]

        random.shuffle(pos_options)
        self.players["p1"]      = {"lives": lives, "pos": pos_options[0]}
        self.players["p2"]      = {"lives": lives, "pos": pos_options[1]}
        if playercount >= 3:
            self.players["p3"]  = {"lives": lives, "pos": pos_options[2]}
        if playercount == 4:
            self.players["p4"]  = {"lives": lives, "pos": pos_options[3]}

    def getExplodeTiles(self, coord):
        #Only + tiles
        #Other function for recursive effect
        pass

    def isBombHere(self, coord):
        return any(lambda bomb: bomb["pos"] == coord)

    def getBombHere(self, coord):
        bombsHere = list(filter(lambda bomb: bomb["pos"] == coord))
        if not bombsHere:
            return None
        else:
            return bombsHere[0]

    def getPlayersHere(self, coord):
        #Return players here
        pass


    def isWalkable(self, coord):
        (x,y) = coord
        return self.board[x][y] == Empty and not isBombHere(coord)

    def onBoard(self, coord):
        return 0 <= coord[0] < self.dims[0] and 0 <= coord[1] < self.dims[1]

    def get(self, coord):
        return self.board[coord[0]][coord[1]]

    def set(self, coord, val):
        self.board[coord[0]][coord[1]] = val

    def gameover(self):
        return livePlayerCount <= 1

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
    return lbRecv(client["socket"], client["recvbuffer"])


class GameRunner(Thread):  
    #implement timeouts

    #combineer socket en recvbuffer in een object?
    #name, socket, addr
    def __init__(self, clients, viz = None, spectator = None):
        super(GameRunner, self).__init__()

        self.clients = clients
        self.viz = VisualiserWrapper(viz)
        self.spectator = spectator

        for client in self.clients:
            client["recvbuffer"] = RecvBuffer()
            #client["socket"].settimeout(None)

        self.BOARDSIZE = (15,)*2
        self.board = Board(self.BOARDSIZE)
        self.board.fillBoard1()
        self.board.placePlayers(len(clients),LIVES)

        for p, pinfo in self.board.players.items():
            pos = pinfo ["pos"]
            self.viz.syncUpdate(Visualiser.addFloatByKey, p, pos, 'CHAR{}'.format(p.lstrip("p")))

        self.updatePlayerInfoViz()
        self.updateMapViz()
        

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


    def explodePlus(self, coord):
        self.viz.syncUpdate(Visualiser.changeByKey, coord, 'FIRE')
        #self.killCoord(*coord)
        deadtrees = []
        hitbombs = []

        for y in range(coord[1]-1,-1,-1):
            (cont, treelist, bomblist) = self.explodeHere(coord[0], y)
            hitbombs.extend(bomblist)
            if not cont:
                break
        deadtrees.extend(treelist)
        for y in range(coord[1]+1,self.BOARDSIZE[1]):
            (cont, treelist, bomblist) = self.explodeHere(coord[0], y)
            hitbombs.extend(bomblist)
            if not cont:
                break
        deadtrees.extend(treelist)
        for x in range(coord[0]-1,-1,-1):
            (cont, treelist, bomblist) = self.explodeHere(x, coord[1])
            hitbombs.extend(bomblist)
            if not cont:
                break
        deadtrees.extend(treelist)
        for x in range(coord[0]+1,self.BOARDSIZE[0]):
            (cont, treelist, bomblist) = self.explodeHere(x, coord[1])
            hitbombs.extend(bomblist)
            if not cont:
                break
        deadtrees.extend(treelist)
        #print("CHAIN TO ",hitbombs)
        return (deadtrees, hitbombs)


    def explodeHere(self, x, y):
        #Return whether to continue the explosion in this direction, possible tree to remove, bombs to detonate
        #return False and possible tree to remove if ended
        #return True if continue
        #self.killCoord(x,y)

        if self.board.board[y][x].unbreakable:
            return (False, [], [])
        elif self.board.board[y][x] == Tile.Tree:
            return (False, [(x,y)], [])
        else:
            self.viz.syncUpdate(Visualiser.changeByKey, (x,y), 'FIRE')

            bombsHere = list(filter(lambda bomb: bomb["pos"] == (x,y), self.board.bombs))
            if len(bombsHere) > 0:
                self.removeBombCoord((x,y))
            return (True, [], bombsHere)

    def killCoord(self, x, y):
        #TODO FIX THIS (bad)
        foundHere = list(filter((lambda t: self.board.players[t]['lives'] > 0 and self.board.players[t]['pos'] == (x,y)),self.board.players))
        for p in foundHere:
            print("Killing",p)
            self.viz.syncUpdate(Visualiser.addFloatByKey, p, self.board.players[p]['pos'],'SKULL')
            self.board.players[p]['lives'] = 0

    def removeBombCoord(self, coord):
        self.board.bombs = list(filter(lambda bomb: bomb["pos"] != coord, self.board.bombs))
        self.viz.syncUpdate(Visualiser.removeBomb, coord)
        print("Removed bomb at {}".format(coord))

    #TODO LOOK AT THIS
    def updateMapViz(self):
        for y in range(self.BOARDSIZE[1]):
            for x in range(self.BOARDSIZE[0]):
                self.viz.syncUpdate(Visualiser.changeByKey, (x,y), {
                                        Tile.Water:'WATER',
                                        Tile.Mountain:'MOUNTAIN',
                                        Tile.Tree:'TREE',
                                        Tile.Empty:'DOT2'
                                        }[self.board.board[y][x]])
        self.viz.syncUpdate(Visualiser.drawScreen)
        print("Screen should update now")

    def updatePlayerInfoViz(self):
        for p, pinfo in self.board.players.items():
            pos = pinfo ["pos"]
            lives = pinfo["lives"]
            pNo = int(p.lstrip("p")) - 1
            self.viz.syncUpdate(Visualiser.setPlayerInfo, pNo, (self.clients[pNo]["name"] ,lives, False))

    def setPlayersViz(self):
        images = list(map((lambda x: 'CHAR{}'.format(x)), list(range(1,5))))
        print(images)
        random.shuffle(images)

        for ix, (player,info) in enumerate(self.board.players.items()):
            print(player)
            self.viz.syncUpdate(Visualiser.addFloatByKey, player,info['pos'], images[ix])
        self.viz.syncUpdate(Visualiser.drawScreen)

    def updatePlayerViz(self):
        moves = {}
        for player, info in self.board.players.items():
            moves[player] = info['pos']
        self.viz.syncUpdate(Visualiser.animateWalk, moves)

    #Look at this
    def clearFires(self):
        for y in range(self.BOARDSIZE[1]):
            for x in range(self.BOARDSIZE[0]):
                if self.board.board[y][x] == Tile.Empty:
                    self.viz.syncUpdate(Visualiser.changeByKey, (x,y), 'DOT2')
        '''
        for p, info in self.board.players.items():
            if info == None:
                self.viz.syncUpdate(Visualiser.removeFloat, p)
        '''

    #Look at this
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
        self.viz.syncUpdate(Visualiser.animateWaterIn, self.waterlevel)

    def doAct(self):
        #Clear fire, trees and skulls
        #self.clearFires()
        
        #Request action
        for client in self.clients:
            writeTo(client, "REQUEST MOVE")

        '''
        responses = []
        #Receive action
        for client in self.clients:
            response = readFrom(client)
            print(client["name"], response)
        print("Done receiving")
        

        #Parse, verify and do

        
        #Perform actions
        for player, info in self.board.players.items():
            (x,y) = self.board.players[player]['pos']
            choices = ([(1,0)] if x != 13 else []) + ([(0,1)] if y != 13 else []) + ([(-1,0)] if x != 1 else []) + ([(0,-1)] if y != 1 else [])
            choices = list(filter((lambda coord: self.board.board[y+coord[1]][x+coord[0]] == Tile.Empty), choices))
            (dx, dy) = random.choice(choices)
            self.board.players[player]['pos'] = (x + dx, y + dy)
        
        self.updatePlayerViz()
        '''

    def tickBombs(self):
        for bomb in self.board.bombs:
            bomb["timer"] = bomb["timer"] - 1

            if bomb['timer'] == 1:
                for client in self.clients:
                    writeTo(client, "UPDATE BOMB PRIMED {}".format(bomb["pos"]))
                self.viz.syncUpdate(Visualiser.primeBomb, bomb['pos'])

    def detonateBombs(self):
        boomlist = list(filter(lambda bomb: bomb["timer"] <= 0, self.board.bombs))
        removeTiles = []

        while len(boomlist) > 0:
            curBoomLoc = boomlist.pop(0)["pos"]
            self.removeBombCoord(curBoomLoc)
            for client in self.clients:
                writeTo(client, "UPDATE BOMB EXPLODED {}".format(curBoomLoc))

            (deadtrees, hitbombs) = self.explodePlus(curBoomLoc)
            boomlist.extend(hitbombs)
            removeTiles.extend(deadtrees)
        
        for tree in removeTiles:
            (x,y) = tree
            self.board.board[y][x] = Tile.Empty
            self.viz.syncUpdate(Visualiser.changeByKey, tree, 'BURNTREE')
            for client in self.clients:
                writeTo(client, "UPDATE TILE GONE {}".format(tree))

        self.viz.syncUpdate(Visualiser.drawScreen)



    def doBombs(self):
        self.tickBombs()
        self.detonateBombs()
        #self.explode((1, 1))

    def doTurn(self):
        self.clearFires()
        print("time to act")
        self.doAct()
        #time.sleep(1)
        print("time to bomb")
        self.doBombs()
        for client in self.clients:
            writeTo(client, "UPDATE DONE")
        time.sleep(0.5)

    def doConfig(self):
        #Inform names and ids
        for no, client in enumerate(self.clients):
            writeTo(client, "CONFIG YOU p{}".format(no+1))
            for no2, client2 in enumerate(self.clients):
                if no != no2:
                    writeTo(client, "CONFIG PLAYER NAME p{} {}".format(no2+1, client2["name"]))

            #Inform location and lives
            for no2, client2 in enumerate(self.clients):
                character = self.board.players["p{}".format(no2+1)]
                writeTo(client, "CONFIG PLAYER PLACE p{} {}".format(no2+1, character["pos"]))
                writeTo(client, "CONFIG PLAYER LIVES p{} {}".format(no2+1, character["lives"]))

            #Water rounds
            for waterRound in WATERROUNDS:
                writeTo(client, "CONFIG WATER ROUND {}".format(waterRound))
            
            #Map
            for y in range(self.board.dims[1]):
                for x in range(self.board.dims[0]):
                    el = self.board.board[x][y]
                    if el != Tile.Empty:
                        writeTo(client, "CONFIG TILE {} {}".format((x,y), el.name.upper()))
            
            writeTo(client, "START GAME")


    def run(self):
        try:
            print(" versus ".join(map(lambda x: x['name'], self.clients)))

            #informSpectator(self.spectator,"updateTitle True {}".format(self.clientA["name"]))

            #combinations(self.clients, len(self.clients) - 1)
            for client in self.clients:
                writeTo(client,"CHALLENGED BY {}".format("a bunch of others"))
            
            self.waitReady()

            self.doConfig()

            time.sleep(2)

            '''
            self.board.board[7][4] = Tile.Tree
            self.viz.syncUpdate(Visualiser.changeByKey, (4,7), 'TREE')
            self.board.board[7][3] = Tile.Tree
            self.viz.syncUpdate(Visualiser.changeByKey, (3,7), 'TREE')
            
            self.board.bombs.append({'pos':(5,7),'timer':3})
            self.viz.syncUpdate(Visualiser.addBomb, (5,7))
            self.viz.syncUpdate(Visualiser.drawScreen)
            '''
            self.board.bombs.append({'pos':(7,7),'timer':2})
            self.viz.syncUpdate(Visualiser.addBomb, (7,7))
            for client in self.clients:
                writeTo(client,"UPDATE BOMB PLACED {}".format((7,7)))
            self.board.bombs.append({'pos':(9,7),'timer':11})
            self.viz.syncUpdate(Visualiser.addBomb, (9,7))
            for client in self.clients:
                writeTo(client,"UPDATE BOMB PLACED {}".format((9,7)))
                writeTo(client,"UPDATE DONE")
            self.viz.syncUpdate(Visualiser.drawScreen)
            time.sleep(1.1)
            for i in range(5):
                print("TURN {}".format(i))
                self.doTurn()

            self.board.bombs.append({'pos':(7,7),'timer':2})
            self.viz.syncUpdate(Visualiser.addBomb, (7,7))
            for client in self.clients:
                writeTo(client,"UPDATE BOMB PLACED {}".format((7,7)))
                writeTo(client,"UPDATE DONE")
            self.viz.syncUpdate(Visualiser.drawScreen)
            time.sleep(1.1)
            for i in range(5,10):
                print("TURN {}".format(i))
                self.doTurn()
            
            
        except (GameEndException,connClosedException) as e:
            print(e)

        for client in self.clients:
            #client["socket"].close()
            pass

        #informSpectator(self.spectator,"end")
        print("Like tears, in rain. Time to die.")
        time.sleep(1)
        #self.board.players['p1']['pos'] = (7,)*2
        #self.updatePlayerViz()
        #time.sleep(5)
        for i in range(4):
            #self.doWater()
            #v.animateWaterIn(i,None)
            pass
        time.sleep(15)

        print("Match ended")
        

def main():
    viz = Visualiser(True, 1)
    wrapper = VisualiserWrapper(viz)
    gr = GameRunner([{"name":"testerbot"},{"name":"randbot"},{"name":"silentbot"},{"name":"mutebot"}],viz=wrapper)
    gr.run()
    


if __name__ == "__main__":
    main()
