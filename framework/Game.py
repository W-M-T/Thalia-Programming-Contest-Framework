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
WATERROUNDS = [60,80,100,120,140]
BOMBTIMER = 7


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
    STAY    = (0, 0)

    @property
    def isChange(self):
        return self in [Dir.UP, Dir.LEFT, Dir.DOWN, Dir.RIGHT]
    
    

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


    def isBombHere(self, coord):
        return any(map(lambda bomb: bomb["pos"] == coord,self.bombs))

    def getBombHere(self, coord):
        bombsHere = list(filter(lambda bomb: bomb["pos"] == coord))
        if not bombsHere:
            return None
        else:
            return bombsHere[0]

    def isPlayersHere(self, coord):
        playerInfos = list(p[1] for p in self.players.items())
        return any(map(lambda player: player["pos"] == coord, playerInfos))

    def isWalkable(self, coord):
        (x,y) = coord
        return self.board[y][x] == Tile.Empty and not self.isBombHere(coord)

    def onBoard(self, coord):
        return 0 <= coord[0] < self.dims[0] and 0 <= coord[1] < self.dims[1]

    def get(self, coord):
        return self.board[coord[1]][coord[0]]

    def set(self, coord, val):
        self.board[coord[1]][coord[0]] = val

    def getLivePlayerIDs(self):
        return [k for (k,v) in self.players.items() if v["lives"] > 0]



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

        for k, client in enumerate(self.clients):
            client["recvbuffer"] = RecvBuffer()
            client["pID"] = "p{}".format(k+1)
            #client["socket"].settimeout(None)

        self.BOARDSIZE = (15,)*2
        self.board = Board(self.BOARDSIZE)
        self.board.fillBoard1()
        self.board.placePlayers(len(clients),LIVES)

        for p, pinfo in self.board.players.items():
            pos = pinfo["pos"]
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
        deadtrees  = []
        hitbombs   = []
        hitplayers = []

        self.viz.syncUpdate(Visualiser.changeByKey, coord, 'FIRE')
        hitplayers.extend(self.hitPlayerHere(coord))

        for y in range(coord[1]-1,-1,-1):
            (cont, treelist, bomblist, playerlist) = self.explodeHere(coord[0], y)
            deadtrees.extend(treelist)
            hitbombs.extend(bomblist)
            hitplayers.extend(playerlist)
            if not cont:
                break
        for y in range(coord[1]+1,self.BOARDSIZE[1]):
            (cont, treelist, bomblist, playerlist) = self.explodeHere(coord[0], y)
            deadtrees.extend(treelist)
            hitbombs.extend(bomblist)
            hitplayers.extend(playerlist)
            if not cont:
                break
        for x in range(coord[0]-1,-1,-1):
            (cont, treelist, bomblist, playerlist) = self.explodeHere(x, coord[1])
            deadtrees.extend(treelist)
            hitbombs.extend(bomblist)
            hitplayers.extend(playerlist)
            if not cont:
                break
        for x in range(coord[0]+1,self.BOARDSIZE[0]):
            (cont, treelist, bomblist, playerlist) = self.explodeHere(x, coord[1])
            deadtrees.extend(treelist)
            hitbombs.extend(bomblist)
            hitplayers.extend(playerlist)
            if not cont:
                break
        #print("CHAIN TO ",hitbombs)
        return (deadtrees, hitbombs, hitplayers)


    def explodeHere(self, x, y):
        #Return whether to continue the explosion in this direction, possible tree to remove, bombs to detonate
        #return False and possible tree to remove if ended
        #return True if continue

        if self.board.board[y][x].unbreakable:
            return (False, [], [], [])
        elif self.board.board[y][x] == Tile.Tree:
            return (False, [(x,y)], [], [])
        else:
            self.viz.syncUpdate(Visualiser.changeByKey, (x,y), 'FIRE')

            playersHere = self.hitPlayerHere((x,y))
            bombsHere = list(filter(lambda bomb: bomb["pos"] == (x,y), self.board.bombs))
            if len(bombsHere) > 0:
                self.removeBombCoord((x,y))
            return (True, [], bombsHere, playersHere)

    def hitPlayerHere(self, coord):
        (x,y) = coord
        return list(filter((lambda t: self.board.players[t]['lives'] > 0 and self.board.players[t]['pos'] == (x,y)),self.board.players))

    def drownCoord(self, coord):
        (x,y) = coord
        foundHere = list(filter((lambda t: self.board.players[t]['lives'] > 0 and self.board.players[t]['pos'] == (x,y)),self.board.players))
        for p in foundHere:
            #print("Killing",p)
            self.viz.syncUpdate(Visualiser.changeFloatByKey, p, 'SKULL')
            #self.viz.syncUpdate(Visualiser.setPlayerFire, int(p[1:])-1)
            self.board.players[p]['lives'] = 0
            writeTo(self.clients[int(p[1:])-1], "YOU LOST")

            for client in self.clients:
                writeTo(client,"UPDATE PLAYER STATUS {} DEAD (DROWNED)".format(p))

    def dmgPlayer(self, p):
        status = "HIT"
        self.viz.syncUpdate(Visualiser.setPlayerFire, int(p[1:])-1)
        self.board.players[p]['lives'] = self.board.players[p]['lives'] - 1
        if self.board.players[p]['lives'] == 0:
            status = "DEAD"
            self.viz.syncUpdate(Visualiser.changeFloatByKey, p, 'SKULL')
            writeTo(self.clients[int(p[1:])-1], "YOU LOST")
        
        for client in self.clients:
            writeTo(client,"UPDATE PLAYER STATUS {} {}".format(p, status))

    def removeBombCoord(self, coord):
        self.board.bombs = list(filter(lambda bomb: bomb["pos"] != coord, self.board.bombs))
        self.viz.syncUpdate(Visualiser.removeBomb, coord)
        #print("Removed bomb at {}".format(coord))

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
        #print("Screen should update now")

    def updatePlayerInfoViz(self):
        for p, pinfo in self.board.players.items():
            pos = pinfo ["pos"]
            lives = pinfo["lives"]
            pNo = int(p.lstrip("p")) - 1
            self.viz.syncUpdate(Visualiser.setPlayerInfo, pNo, (self.clients[pNo]["name"] ,lives, False))


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
        self.waterlevel += 1

        for client in self.clients:
            writeTo(client, "UPDATE WATER {}".format(self.waterlevel))

        for y in range(self.BOARDSIZE[1]):
            self.removeBombCoord((self.waterlevel, y))
            self.drownCoord((self.waterlevel, y))
            self.board.board[y][self.waterlevel] = Tile.Water

            self.removeBombCoord((self.BOARDSIZE[0] - 1 - self.waterlevel, y))
            self.drownCoord((self.BOARDSIZE[0] - 1 - self.waterlevel, y))
            self.board.board[y][self.BOARDSIZE[0] - 1 - self.waterlevel] = Tile.Water

        for x in range(self.BOARDSIZE[0]):
            self.removeBombCoord((x, self.waterlevel))
            self.drownCoord((x, self.waterlevel))
            self.board.board[self.waterlevel][x] = Tile.Water

            self.removeBombCoord((x, self.BOARDSIZE[1] - 1 - self.waterlevel))
            self.drownCoord((x, self.BOARDSIZE[1] - 1 - self.waterlevel))
            self.board.board[self.BOARDSIZE[0] - 1 - self.waterlevel][x] = Tile.Water
        self.viz.syncUpdate(Visualiser.animateWaterIn, self.waterlevel)

    def doAct(self):
        #Clear fire, trees and skulls
        #self.clearFires()
        
        #Request action
        for client in self.clients:
            writeTo(client, "REQUEST MOVE")

        
        responses = []
        #Receive action
        for client in [aclient for aclient in self.clients if aclient["pID"] in self.board.getLivePlayerIDs()]:
            response = readFrom(client)
            #print(client["name"], response)
            responses.append((client,response))
        #print("Done receiving")
        

        #Parse, verify and do
        walktiles = []
        desiredmoves = []
        placedbombs = []
        for response in responses:
            tokens = response[1].split(" ",1)
            if tokens[0] not in ["WALK","BOMBWALK"]:
                print("Error wrong bot command",response)
                continue
            else:
                if tokens[0] == "BOMBWALK":
                    placedbombs.append(self.board.players[response[0]["pID"]]["pos"])
                if tokens[1] not in Dir.__members__.keys():
                    print("Error wrong direction format",response)
                    continue
                else:
                    delta = Dir[tokens[1]].value
                    #print(delta,Dir[tokens[1]],self.board.players[response[0]["pID"]])
                    walktile = tuple(map(sum,zip(delta,self.board.players[response[0]["pID"]]["pos"])))
                    walktiles.append(walktile)
                    desiredmoves.append((response[0]["pID"],walktile))

        for placedbomb in placedbombs:
            self.board.bombs.append({"pos":placedbomb,"timer":BOMBTIMER+1})
            self.viz.syncUpdate(Visualiser.addBomb, placedbomb)
            for client in self.clients:
                writeTo(client,"UPDATE BOMB PLACED {}".format(placedbomb))

        goodmoves = []
        #print("Desired moves",desiredmoves)
        for desiredmove in desiredmoves:
            othersmoves = list(filter(lambda othermove: othermove != desiredmove, desiredmoves))
            conflictmoves = list(filter(lambda othermove: othermove[1] == desiredmove[1],othersmoves))
            #print(desiredmove,"and others",othersmoves,"give conflicts",conflictmoves)
            if len(conflictmoves) > 0:
                #print("CONFLICT")
                continue
            else:
                if not self.board.isWalkable(desiredmove[1]) or self.board.isPlayersHere(desiredmove[1]):
                    '''
                    if self.board.isBombHere(desiredmove[1]):
                        print("TRIED TO WALK INTO A BOMB")
                    else:
                        print("TRIED TO WALK INTO A {}".format(self.board.get(desiredmove[1]).name))
                    '''
                    continue
                else:
                    goodmoves.append(desiredmove)

        movedict = {}
        for goodmove in goodmoves:
            movedict[goodmove[0]] = goodmove[1]
            self.board.players[goodmove[0]]["pos"] = goodmove[1]
            for client in self.clients:
                writeTo(client,"UPDATE PLAYER LOC {} {}".format(goodmove[0], goodmove[1]))

        self.viz.syncUpdate(Visualiser.animateWalk, movedict)

        self.viz.syncUpdate(Visualiser.drawScreen)


    def tickBombs(self):
        for bomb in self.board.bombs:
            bomb["timer"] = bomb["timer"] - 1

            if bomb['timer'] == 1:
                for client in self.clients:
                    writeTo(client, "UPDATE BOMB PRIMED {}".format(bomb["pos"]))
                self.viz.syncUpdate(Visualiser.primeBomb, bomb['pos'])

    def detonateBombs(self):
        boomlist = list(filter(lambda bomb: bomb["timer"] <= 0, self.board.bombs))
        removeTiles = set()
        hitplayerset = set()

        while len(boomlist) > 0:
            curBoomLoc = boomlist.pop(0)["pos"]
            self.removeBombCoord(curBoomLoc)
            for client in self.clients:
                writeTo(client, "UPDATE BOMB EXPLODED {}".format(curBoomLoc))

            (deadtrees, hitbombs, hitplayers) = self.explodePlus(curBoomLoc)
            boomlist.extend(hitbombs)
            removeTiles = removeTiles.union(deadtrees)
            hitplayerset = hitplayerset.union(hitplayers)
        
        for tree in removeTiles:
            (x,y) = tree
            self.board.board[y][x] = Tile.Empty
            self.viz.syncUpdate(Visualiser.changeByKey, tree, 'BURNTREE')
            for client in self.clients:
                writeTo(client, "UPDATE TILE GONE {}".format(tree))

        for player in hitplayerset:
            #print("Player got hit",player)
            self.dmgPlayer(player)

        self.viz.syncUpdate(Visualiser.drawScreen)



    def doBombs(self):
        self.tickBombs()
        self.detonateBombs()
        self.updatePlayerInfoViz()
        #self.explode((1, 1))

    def doTurn(self, turnNo):
        self.clearFires()
        #print("time to act")
        self.doAct()
        #time.sleep(1)
        #print("time to bomb")
        self.doBombs()
        if turnNo in WATERROUNDS:
            self.doWater()

        for client in self.clients:
            writeTo(client, "UPDATE DONE")

        liveClients = [aclient for aclient in self.clients if aclient["pID"] in self.board.getLivePlayerIDs()] 
        if len(liveClients) <= 1:
            # Game over!
            for client in liveClients:
                writeTo(client, "YOU WON")
            for client in self.clients:
                writeTo(client, "END")
            raise GameEndException("Match ended: Living: {} ({})".format([k["name"] for k in liveClients], " versus ".join(map(lambda x: x['name'], self.clients))))

        time.sleep(0.3)

    def doConfig(self):
        #Inform names and ids
        for client in self.clients:
            writeTo(client, "CONFIG YOU {}".format(client["pID"]))
            for client2 in self.clients:
                if client["pID"] != client2["pID"]:
                    writeTo(client, "CONFIG PLAYER NAME {} {}".format(client2["pID"], client2["name"]))

            #Inform location and lives
            for client2 in self.clients:
                character = self.board.players["{}".format(client2["pID"])]
                writeTo(client, "CONFIG PLAYER PLACE {} {}".format(client2["pID"], character["pos"]))
                writeTo(client, "CONFIG PLAYER LIVES {} {}".format(client2["pID"], character["lives"]))

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

            iteration = 0
            while True:
                #print("TURN {}".format(iteration))
                self.doTurn(iteration)
                iteration = iteration + 1
            
        except (GameEndException,connClosedException) as e:
            print(e)

        print("Match ended")
        

def main():
    viz = Visualiser(True, 1)
    wrapper = VisualiserWrapper(viz)
    gr = GameRunner([{"name":"testerbot"},{"name":"randbot"},{"name":"silentbot"},{"name":"mutebot"}],viz=wrapper)
    gr.run()
    


if __name__ == "__main__":
    main()
