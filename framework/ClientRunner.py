#!/usr/bin/python3

from subprocess import Popen, PIPE, STDOUT
import os
import signal
import socket
import time
import select

#refactor:
#move the parsing and viz update code to another file to keep this runner independent of the game

proc = None
sock = None
linebuffer = []
SHELLMODE = True
RECVCONST = 4096

DEBUG = False

def cleanup():
    if not SHELLMODE and proc is not None:
        proc.kill()
    if proc is not None:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    if debugfile is not None:
        debugfile.close()


import atexit
atexit.register(cleanup)


def sayToServer(data):
    global sock

    sock.send((data + "\n").encode("utf-8"))

def lbrecv():#Line buffered receive
    #unhandled case is if the socket receive ends in the middle of a message, wich should only happen if there are more than 4096 bytes in the receive buffer
    global sock, linebuffer

    if linebuffer:
        return linebuffer.pop(0)
    else:
        bytedata = sock.recv(RECVCONST)
        if len(bytedata) == 0:#Connection was closed
            raise Exception("Connection was closed")
        data = bytedata.decode("utf-8").rstrip("\n").split("\n")
        ret = data.pop(0)
        linebuffer.extend(data)
        return ret


def establish_connection(server, port, teamname, roomkey):
    global sock

    try:
        sock = socket.create_connection((server,port))
        sayToServer("CLIENT NAME {}".format(teamname))
        sayToServer("CLIENT KEY {}".format(roomkey))

    except ConnectionRefusedError:
        print("[-] Connection refused")
        exit()

def waitForChallenge():
    global sock

    print("[*] Waiting for challenger")

    while True:
        
        s = lbrecv()
        if s.find("PING") == 0:
            sayToServer("PONG")
            continue
        maybeother = stripFormat("CHALLENGED BY ",s)
        if maybeother is not None:
            return maybeother



PROT_SERVERBOTSERVER = ["REQUEST ACTION SHOT"]
PROT_SERVER          = ["UPDATE ", "GAME RESULT "]

def getDepth(data):
    if data in PROT_SERVERBOTSERVER:
        return 3
    elif any([data.find(x) == 0 for x in PROT_SERVER]):
        return 1
    else:
        return 2

class gameEnded(Exception):
    pass

def testEnd(data):
    if data.find("GAME RESULT ") == 0:
        print("GAME OVER")
        raise gameEnded

def becomeLink(viz):
    global proc, sock
    
    end = False
    try:

        while True:
            #print("LOOPING")

            #SERVER -> BOT
            data = lbrecv()
            if DEBUG:
                print(data)
            else:
                print(data, file=proc.stdin, flush=True)
            updateViz(viz,data)#(Voor UPDATE command)

            testEnd(data)

            flow = getDepth(data)

            if flow >= 2:
                #BOT -> SERVER
                bot_resp = input() if DEBUG else proc.stdout.readline().rstrip("\n")
                #print(bot_resp)
                sayToServer(bot_resp)
                updateViz(viz,data,response=bot_resp)#(Voor PLACE command)

                testEnd(data)

            if flow >= 3:
                #SERVER -> BOT AGAIN
                data_result = lbrecv()
                if DEBUG:
                    print(data_result)
                else:
                    print(data_result, file=proc.stdin, flush=True)
                updateViz(viz,data,response=bot_resp,result=data_result)#(Voor SHOOT -> RESULT command)

                testEnd(data)

    except gameEnded:
        pass

            
    print("Link stopped")

shiplist = []

def getShipHit(viz,coord):
    global shiplist


    for (shipstart,shipend) in shiplist:
        if shipstart[0] == shipend[0]:#Vertical
            if shipstart[0] != coord[0]:
                continue
            top = max(shipstart[1],shipend[1])
            bot = min(shipstart[1],shipend[1])
            #print(bot,top)
            if coord[1] == top:
                return viz.SHIP_HIT_TOP
            elif coord[1] == bot:
                return viz.SHIP_HIT_BOT
            elif coord[1] in range(bot + 1, top):
                return viz.SHIP_HIT_MID
            
            
        else:#Horizontal
            if shipstart[1] != coord[1]:
                continue
            left = min(shipstart[0],shipend[0])
            right = max(shipstart[0],shipend[0])
            #print(left,right)
            if coord[0] == left:
                return viz.SHIP_HIT_LEFT
            elif coord[0] == right:
                return viz.SHIP_HIT_RIGHT
            elif coord[0] in range(left + 1, right):
                return viz.SHIP_HIT_MID

    return viz.CROSS


def updateViz(viz, init, response = None, result = None):
    global shiplist
    
    if viz is not None:
        #UPDATE COMMAND
        maybeUpdate = stripFormat("UPDATE ", init)
        if maybeUpdate is not None:
            maybeGotShot   = stripFormat("GOTSHOT ",maybeUpdate)
            if maybeGotShot is not None:
                maybeCoord = parseCoord(maybeGotShot)
                if maybeCoord is not None:
                    viz.change(True,maybeCoord,getShipHit(viz,maybeCoord))
                #malformed coord
                return

            maybeGotIsland = stripFormat("GOTISLAND ",maybeUpdate)
            if maybeGotIsland is not None:
                maybeCoord = parseCoord(maybeGotIsland)
                if maybeCoord is not None:
                    viz.change(True, maybeCoord, viz.ISLAND)
                    return
                #malformed coord
                return
            
            #malformed update
            return

        if response is not None:
            #PLACE COMMAND
            maybePlace = stripFormat("PLACE ",response)
            if maybePlace is not None:

                maybeShip = stripFormat("SHIP ",maybePlace)
                if maybeShip is not None:
                    split = maybeShip.split(" ")
                    if len(split) != 2:
                        pass#malformed command
                    maybeCoordStart = parseCoord(split[0])
                    maybeCoordEnd = parseCoord(split[1])
                    if maybeCoordStart is not None and maybeCoordEnd is not None:
                        shiplist.append((maybeCoordStart,maybeCoordEnd))
                        viz.placeShip(True,maybeCoordStart,maybeCoordEnd)
                        return
                    #malformed coords

                maybeIsland = stripFormat("ISLAND ",maybePlace)
                if maybeIsland is not None:
                    maybeCoord = parseCoord(maybeIsland)
                    if maybeCoord is not None:
                        viz.change(False,maybeCoord,viz.ISLAND)
                        return
                    #malformed coord
                    return

                #malformed place
                return

            #SHOOT->RESULT
            maybeShoot = stripFormat("SHOOT ",response)
            if maybeShoot is not None and result is not None:
                maybeCoord = parseCoord(maybeShoot)
                maybeResult = stripFormat("RESULT ",result)
                if maybeCoord is not None and maybeResult is not None:
                    maybeHit = stripFormat("HIT",maybeResult)
                    if maybeHit is not None:
                        viz.change(False,maybeCoord,viz.BOOM)
                        return
                    maybeMiss = stripFormat("MISS",maybeResult)
                    if maybeMiss is not None:
                        viz.change(False,maybeCoord,viz.CROSS)
                        return
                    #malformed result
                    return


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

def stripFormat(form,data):
    if data.find(form) == 0:
        return data.replace(form,"",1)
    else:
        return None

import random
def readConfig():
    with open("./config","r") as conf:
        s = conf.read().split("\n")
        s = list(filter(lambda x: not (x.isspace() or x == ""), s))
        s = [x.strip() for x in s]
        try:
            teamname      = s[s.index("# TEAM NAME:") + 1]
            viz           = s[s.index("# VISUALISER ENABLED:") + 1] == "1"
            debug         = s[s.index("# WRITE BOT STDERR TO FILE:") + 1] == "1"
            runcommand    = s[s.index("# BOT RUNNING COMMAND:") + 1]
            (server,port) = s[s.index("# SERVER ADDRESS:") + 1].split(":")
            return (teamname+str(random.randrange(99)), viz, debug, runcommand,server,port)

        except (ValueError, IndexError):
            print("[-] Config file could not be read")
            exit()

def work():
    global proc, sock, debugfile

    print("[+] Starting client")
    (team, viz_enabled, debug_on, command, server, port) = readConfig()
    print(team)

    if debug_on:
        debugfile = open("./stderr.txt","w")
        #Write initial line containing time
    proc = Popen(command, shell=SHELLMODE, stdin=PIPE, stdout=PIPE, stderr=debugfile if debug_on else DEVNULL, bufsize=1, universal_newlines=True, preexec_fn=os.setsid)

    print("[?] Enter room key:\n> ",end="")
    roomkey = input().strip()

    establish_connection(server, port, team, roomkey)

    otherteam = waitForChallenge()

    print("[+] Challenged by {}".format(otherteam))

    #Move to seperate function
    if viz_enabled:
        try:
            from Visualiser import Visualiser
            viz = Visualiser(2,True,False)
            viz.updateTitle("You ({})".format(team),"Other ({})".format(otherteam))

            print("[+] UI running")
        except Exception as e:
            print("[-] Got an error:")
            print(e)
            print(proc.stderr.read(), end="")
    else:
        viz = None

    print("READY")
    sayToServer("READY")
    
    becomeLink(viz=viz)
    try:
        time.sleep(10)#Should maybe be an option?
    except KeyboardInterrupt:
        pass

    print("[*] Client ended")
    

def main():
    try:
        work()
    except KeyboardInterrupt:
        print("\n[-] Force terminated")

if __name__ == "__main__":
    main()