#!/usr/bin/python3

from enum import Enum, IntEnum
from threading import Thread
import random
import time

from Visualiser import Visualiser

RECVCONST = 4096
TURNTIMEOUT      = 2.0
MINTURNTIME      = 0.5

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

class ShipSide(Enum):
    TOP   = 0
    BOT   = 1
    LEFT  = 2
    RIGHT = 3
    MID   = 4

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

            #print("WEIRDEST BUG EVER") #UNCOMMENT THIS TO SEE A BLACK MAGIC BUG
            informSpectator(self.spec, "change {} {} {}".format(self.ownviz,coord,"island"))
            #print("AFTER")
            if self.viz is not None:
                self.viz.syncUpdate(Visualiser.change,[self.ownviz,coord,self.viz.ISLAND])
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

                informSpectator(self.spec, "placeShip {} {} {}".format(self.ownviz,start,end))
                if self.viz is not None:
                    self.viz.syncUpdate(Visualiser.placeShip,[self.ownviz,start,end])

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

                informSpectator(self.spec, "placeShip {} {} {}".format(self.ownviz,start,end))
                if self.viz is not None:
                    self.viz.syncUpdate(Visualiser.placeShip,[self.ownviz,start,end])

            else:
                return (False,"NOT HORIZONTAL OR VERTICAL")
        else:
            return (False,"NOT ON BOARD")
        return (True,None)

    def shoot(self,coord):
        (hit,sunkship) = self.doHit(coord)
        #print(hit,sunkship)

        informSpectator(self.spec,"change {} {} {}".format(self.ownviz,coord,"hit" if hit else "miss"))
        if self.viz is not None:
            img = self.viz.CROSS
            if hit:
                img = self.getHitImg(self.viz,self.getShipHitSide(coord))
            self.viz.syncUpdate(Visualiser.change,[self.ownviz, coord, img])
            
        return (hit,sunkship)

    def doHit(self, coord):
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

    def getHitImg(self,viz,side):#refactor: use this in clientrunner too
        opts = {ShipSide.TOP:   viz.SHIP_HIT_TOP,
                ShipSide.BOT:   viz.SHIP_HIT_BOT,
                ShipSide.LEFT:  viz.SHIP_HIT_LEFT,
                ShipSide.RIGHT: viz.SHIP_HIT_RIGHT,
                ShipSide.MID:   viz.SHIP_HIT_MID
        }
        return opts[side]


    def getShipHitSide(self,coord):
        for (shipstart,shipend) in self.shiplist:
            if shipstart[0] == shipend[0]:#Vertical
                if shipstart[0] != coord[0]:
                    continue
                top = max(shipstart[1],shipend[1])
                bot = min(shipstart[1],shipend[1])
                
                if coord[1] == top:
                    return ShipSide.TOP
                elif coord[1] == bot:
                    return ShipSide.BOT
                elif coord[1] in range(bot + 1, top):
                    return ShipSide.MID
                
                
            else:#Horizontal
                if shipstart[1] != coord[1]:
                    continue
                left = min(shipstart[0],shipend[0])
                right = max(shipstart[0],shipend[0])
                
                if coord[0] == left:
                    return ShipSide.LEFT
                elif coord[0] == right:
                    return ShipSide.RIGHT
                elif coord[0] in range(left + 1, right):
                    return ShipSide.MID



def writeTo(client,data):
    try:
        #print("@{}\t".format(client["name"]),end="")
        #print(data)
        client["socket"].send((data+"\n").encode("utf-8"))
        return True
    except Exception as e:
        print(e)
        return False

def informSpectator(spec, text):
    #print("spectator is",spec)
    try:
        if spec is not None and not spec == "None":#Ugly hack
            spec.send((text+"\n").encode("utf-8"))
    except Exception as e:
        pass

class connClosedException(Exception):
    pass

def readFrom(client):
    linebuffer = client["linebuffer"]
    sock       = client["socket"]

    if linebuffer:
        return linebuffer.pop(0)
    else:
        #print("{}: ".format(client["name"]),end="")
        bytedata = sock.recv(RECVCONST)
        if len(bytedata) == 0:#Connection was closed
            raise connClosedException("Connection from {} was closed".format(client["name"]))
        data = bytedata.decode("utf-8").rstrip("\n").split("\n")
        #print(data)
        #data = bytedata.rstrip("\n").split("\n")
        ret = data.pop(0).rstrip(" ")
        linebuffer.extend(data)
        #print(ret)
        return ret

def stripFormat(form,data):
    if data.find(form) == 0:
        return data.replace(form,"",1)
    else:
        return None

def parseCoord(data):
    if data[0] == '(' and data[-1] == ')':
        data = data[1:-1]
        data = data.split(",")
        #print("coords parsed:",data)
        if len(data) == 2:
            try:   
                (a,b) = (int(data[0]),int(data[1]))
                if 0 <= a < 10 and 0 <= b < 10:
                    return (a,b)
                else:
                    return None
            except ValueError:
                return None
        else:
            return None
    else:
        return None

class GameRunner(Thread):  
    #implement timeouts


    #teamname, socket, addr
    def __init__(self, clientA, clientB, viz = None, spectator = None):
        super(GameRunner, self).__init__()
        self.clientA = clientA
        self.clientB = clientB

        self.clientA["linebuffer"] = []
        self.clientB["linebuffer"] = []

        self.clientA["board"] = Board((10,10), viz = viz, spec = spectator, own = True)
        self.clientB["board"] = Board((10,10), viz = viz, spec = spectator, own = False)
        
        self.clientA["socket"].settimeout(None)
        self.clientB["socket"].settimeout(None)

        self.turn = random.randint(0,1)
        self.end  = False

        self.spectator = spectator
            

    def turnClient(self):
        return [self.clientA,self.clientB][self.turn]

    def otherClient(self):
        return [self.clientA,self.clientB][1 - self.turn]

    def disqualify(self,reason):
        writeTo(self.turnClient(),"GAME RESULT YOU LOST (DISQUALIFIED: {})".format(reason))
        writeTo(self.otherClient(), "GAME RESULT YOU WON")

        raise GameEndException("{} was disqualified!! Reason: {}".format(self.turnClient()["name"],reason))

    def handleIsland(self,data):
        #print("data {} enddata".format(data))
        #print("HANDLING")
        maybeIsland = stripFormat("PLACE ISLAND ",data)
        if maybeIsland is not None:
            maybeCoord = parseCoord(maybeIsland)
            if maybeCoord is not None:
                if not self.otherClient()["board"].placeIsland(maybeCoord):
                    self.disqualify("INVALID ISLAND LOCATION")
                return maybeCoord
            else:
                self.disqualify("INVALID COORDINATE")
        else:
            self.disqualify("INVALID ISLAND PLACING COMMAND")

    def handleShip(self,data):
        maybeShip = stripFormat("PLACE SHIP ",data)
        if maybeShip is not None:
            split = maybeShip.split(" ")
            if len(split) != 2:
                self.disqualify("INVALID COORDINATES")
            maybeStart = parseCoord(split[0])
            maybeEnd = parseCoord(split[1])
            if maybeStart is None or maybeEnd is None:
                self.disqualify("INVALID COORDINATES")

            (success,reason) = self.turnClient()["board"].placeShip(maybeStart,maybeEnd)
            if not success:
                self.disqualify("INVALID SHIP LOCATION - {}".format(reason))
        else:
            self.disqualify("INVALID SHIP PLACING COMMAND")

    def handleShot(self,data):
        maybeShoot = stripFormat("SHOOT ",data)
        if maybeShoot is not None:
            maybeCoord = parseCoord(maybeShoot)
            if maybeCoord is not None:
                return (maybeCoord, *self.otherClient()["board"].shoot(maybeCoord))#Here the bool doesn't indicate success of the command, but hit or miss of the shot. The coord being parsed is already enough to guarantee a valid shot
                
            else:
                self.disqualify("INVALID COORDINATES")

        else:
            self.disqualify("INVALID SHOOTING COMMAND")

    def waitReady(self):
        rdyA = readFrom(self.clientA).find("READY") == 0
        rdyB = readFrom(self.clientB).find("READY") == 0
        if not (rdyA and rdyB):
            raise GameEndException("Never readied up")


    def doIslands(self):
        for i in range(0,4):
            for t in range(0,2):
                self.turn = t

                time_start = time.time()

                writeTo(self.turnClient(),"REQUEST ACTION ISLAND")
                response = readFrom(self.turnClient())

                islandcoord = self.handleIsland(response)

                writeTo(self.otherClient(),"UPDATE GOTISLAND {}".format(islandcoord))

                time_response = time.time()
                delta = time_response - time_start
                if delta < MINTURNTIME:
                    time.sleep(MINTURNTIME - delta)

    def doShips(self):
        total = sum([k.count for k in list(Ship)])
        for cur in range(total):
            for t in range(0,2):
                self.turn = t

                time_start = time.time()

                writeTo(self.turnClient(),"REQUEST ACTION SHIP")
                response = readFrom(self.turnClient())

                self.handleShip(response)

                time_response = time.time()
                delta = time_response - time_start
                if delta < MINTURNTIME:
                    time.sleep(MINTURNTIME - delta)

    def doBattle(self):
        while not self.end:
            for t in range(0,2):
                self.turn = t

                time_start = time.time()

                #print("BATTLE")
                writeTo(self.turnClient(),"REQUEST ACTION SHOT")
                response = readFrom(self.turnClient())

                (coord,hit,sunk) = self.handleShot(response)
                result = "RESULT MISS" if not hit else ("RESULT HIT" + (" YOUSUNKMY " + sunk.name.upper() if sunk is not None else ""))
                writeTo(self.turnClient(),result)
                writeTo(self.otherClient(),"UPDATE GOTSHOT {}".format(coord))
                
                if self.otherClient()["board"].gameover():
                    print("{} won against {}".format(
                            self.turnClient()["name"],
                            self.otherClient()["name"]))
                    writeTo(self.turnClient(),"GAME RESULT YOU WON")
                    writeTo(self.otherClient(),"GAME RESULT YOU LOST")
                    self.end = True
                    break


                time_response = time.time()
                delta = time_response - time_start
                if delta < MINTURNTIME:
                    time.sleep(MINTURNTIME - delta)

    def run(self):
        try:
            print(self.clientA["name"], "versus", self.clientB["name"])

            informSpectator(self.spectator,"updateTitle True {}".format(self.clientA["name"]))
            informSpectator(self.spectator,"updateTitle False {}".format(self.clientB["name"]))
            if self.clientA["board"].viz is not None:
                self.clientA["board"].viz.syncUpdate(Visualiser.updateTitle, [self.clientA["name"],self.clientB["name"]])

            writeTo(self.clientA,"CHALLENGED BY {}".format(self.clientB["name"]))
            writeTo(self.clientB,"CHALLENGED BY {}".format(self.clientA["name"]))

            self.waitReady()
            self.doIslands()
            self.doShips()
            self.doBattle()
            
            
        except (GameEndException,connClosedException) as e:
            print(e)

        self.clientA["socket"].close()
        self.clientB["socket"].close()

        informSpectator(self.spectator,"end")
        if self.clientA["board"].viz is not None:
            time.sleep(5)
            self.clientA["board"].viz.syncUpdate(Visualiser.resetBoth, [])
            self.clientA["board"].viz.syncUpdate(Visualiser.updateTitle, ["",""])
        

def main():
    viz = Visualiser(1,True,True)#None#
    gr = GameRunner({"name":"testerbot"},{"name":"randbot"},viz=viz)
    gr.run()
    


if __name__ == "__main__":
    main()
