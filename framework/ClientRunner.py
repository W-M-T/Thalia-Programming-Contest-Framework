#!/usr/bin/env python3

from subprocess import Popen, PIPE, STDOUT, DEVNULL
from queue import Queue, Empty
from threading import Thread, Event
import sys
import select
import os
import signal
import socket
import time
import select
from argparse import ArgumentParser
import configparser
from Util import lbRecv, stripFormat, parseCoord, sockSend, RecvBuffer
from Visualiser import Visualiser, VisualiserWrapper
from Game import Dir

#refactor:
#move the parsing and viz update code to another file to keep this runner independent of the game

proc = None
sock = None
recvbuffer = RecvBuffer()
SHELLMODE = True

DEBUG = False
debugfile = None

def cleanup():
    if not SHELLMODE and proc is not None:
        proc.kill()
    if proc is not None:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    if debugfile is not None:
        debugfile.close()


import atexit
atexit.register(cleanup)

def print_stderr(out, startEvent): #Blocking, so done in another thread
    global proc

    startEvent.wait()
    for line in iter(out.readline, b''):
        if len(line) == 0:
            break
        print("\033[0;33mBOT STDERR >>",line.rstrip("\n"), end="\033[0m\n")
    out.close()


def sayToServer(data):
    global sock

    sockSend(sock, data)


def establish_connection(server, port, teamname, roomkey):
    global sock

    try:
        sock = socket.create_connection((server,port))
        print("[+] Connection established")
        sayToServer("CLIENT NAME {}".format(teamname))
        sayToServer("CLIENT KEY {}".format(roomkey))

    except ConnectionRefusedError:
        print("[-] Connection refused")
        exit()


def waitForChallenge():
    global sock, recvbuffer

    print("[*] Waiting for challenger")

    while True:
        
        s = lbRecv(sock, recvbuffer)
        print(s)
        if s.find("PING") == 0:
            sayToServer("PONG")
            continue
        maybeother = stripFormat("CHALLENGED BY ",s)
        if maybeother is not None:
            return maybeother


class gameEnded(Exception):
    pass


def testDead(data):
    if data.find("YOU LOST") == 0:
        #print("YOU DIED!")
        return True

def testEnd(data):
    if data.find("YOU WON") == 0 or data.find("END") == 0:
        print("GAME OVER:",data)
        time.sleep(2)
        raise gameEnded

def isRequest(data):
    return data.find("REQUEST MOVE") == 0

def dontGiveBot(data):
    return data.find("UPDATE DONE") == 0 or data.find("UPDATE BOMB PRIMED") == 0 or testDead(data)#Not part of the official protocol, just for the visualiser


def updateViz(viz,vizbuffer,waterbuffer,data): #No parsing error handling for server data (has to be correct as a part of the framework)
    global team

    maybeConfig = stripFormat("CONFIG ", data)
    if maybeConfig is not None:

        maybeTile = stripFormat("TILE ", maybeConfig)
        if maybeTile is not None:
            tokens = maybeTile.split(") ",1)
            maybeCoord = parseCoord(tokens[0]+")")
            lookup = {
                "WATER" : "WATER",
                "MOUNTAIN" : "MOUNTAIN",
                "TREE" : "TREE",
                "EMPTY" : "DOT2"
            }
            #print(maybeCoord,lookup[tokens[1]])
            #print(viz.viz)
            viz.syncUpdate(Visualiser.changeByKey, maybeCoord, lookup[tokens[1]])
            return

        maybeName = stripFormat("PLAYER NAME ", maybeConfig)
        if maybeName is not None:
            tokens = maybeName.split(" ")
            pNo = int(tokens[0][1:]) - 1
            viz.syncUpdate(Visualiser.setPlayerName, pNo, tokens[1])
            return

        maybeLives = stripFormat("PLAYER LIVES ", maybeConfig)
        if maybeLives is not None:
            tokens = maybeLives.split(" ")
            pNo = int(tokens[0][1:]) - 1
            viz.syncUpdate(Visualiser.setPlayerLives, pNo, int(tokens[1]))
            return

        maybePlace = stripFormat("PLAYER PLACE ", maybeConfig)
        if maybePlace is not None:
            tokens = maybePlace.split(" ", 1)
            pID = tokens[0]
            coord = parseCoord(tokens[1])
            viz.syncUpdate(Visualiser.addFloatByKey, pID, coord, "CHAR{}".format(tokens[0][1:]))
            return

        maybeYou = stripFormat("YOU ", maybeConfig)
        if maybeYou is not None:
            pNo = int(maybeYou[1:]) - 1
            viz.syncUpdate(Visualiser.setPlayerName, pNo, team)
            return

    maybeStart = stripFormat("START GAME", data)
    if maybeStart is not None:
        viz.syncUpdate(Visualiser.drawScreen)
        return

    maybeUpdate = stripFormat("UPDATE ", data)
    if maybeUpdate is not None:

        maybeDone = stripFormat("DONE", maybeUpdate)
        if maybeDone is not None:
            viz.syncUpdate(Visualiser.drawScreen)
            movedict = {}
            for bufitem in vizbuffer:
                movedict[bufitem[0]] = bufitem[1]
            #time.sleep(0.3)
            #viz.syncUpdate(Visualiser.clearFire)
            viz.syncUpdate(Visualiser.animateWalk, movedict)
            vizbuffer = []
            return

        maybePlayerStatus = stripFormat("PLAYER STATUS ", maybeUpdate)
        if maybePlayerStatus is not None:
            tokens = maybePlayerStatus.split(" ", 1)
            pID = int(tokens[0][1:]) - 1
            status = tokens[1]
            if status == "HIT":
                viz.syncUpdate(Visualiser.decrPlayerLives, pID)
            else: #Dead per definition
                viz.syncUpdate(Visualiser.setPlayerLives, pID, 0)
                viz.syncUpdate(Visualiser.changeFloatByKey, "p{}".format(pID+1), 'SKULL')
            return

        maybePlayerLoc = stripFormat("PLAYER LOC ", maybeUpdate)
        if maybePlayerLoc is not None:
            tokens = maybePlayerLoc.split(" ", 1)
            pID = tokens[0]
            coord = parseCoord(tokens[1])
            vizbuffer.append((pID, coord))
            return

        maybeBombPlaced = stripFormat("BOMB PLACED ", maybeUpdate)
        if maybeBombPlaced is not None:
            coord = parseCoord(maybeBombPlaced)
            viz.syncUpdate(Visualiser.addBomb, coord)
            return

        maybeBombExploded = stripFormat("BOMB EXPLODED ", maybeUpdate)
        if maybeBombExploded is not None:
            coord = parseCoord(maybeBombExploded)
            viz.syncUpdate(Visualiser.explode, coord)
            return

        maybeBombPrimed = stripFormat("BOMB PRIMED ", maybeUpdate)
        if maybeBombPrimed is not None:
            coord = parseCoord(maybeBombPrimed)
            viz.syncUpdate(Visualiser.primeBomb, coord)
            return

        maybeTileGone = stripFormat("TILE GONE ", maybeUpdate)
        if maybeTileGone is not None:
            coord = parseCoord(maybeTileGone)
            viz.syncUpdate(Visualiser.changeByKey, coord, "BURNTREE")
            return

        maybeWaterRound = stripFormat("WATER", maybeUpdate)
        if maybeWaterRound is not None:
            inset = int(maybeWaterRound)
            waterbuffer.append(inset)

    maybeMove = stripFormat("REQUEST MOVE", data)
    if maybeMove is not None:
        viz.syncUpdate(Visualiser.clearFire)
        viz.syncUpdate(Visualiser.drawScreen)
        if len(waterbuffer) > 0:
            inset = waterbuffer.pop(0)
            viz.syncUpdate(Visualiser.animateWaterIn, inset)
        waterbuffer = [] # not needed?
        return

def finalWater(viz, waterbuffer):
    viz.syncUpdate(Visualiser.clearFire)
    viz.syncUpdate(Visualiser.drawScreen)
    if len(waterbuffer) > 0:
        inset = waterbuffer.pop(0)
        viz.syncUpdate(Visualiser.animateWaterIn, inset)



def becomeLink(viz):
    global proc, sock

    vizbuffer = []
    waterbuffer = []
    playerDead = False

    try:

        while True:
            #print("LOOPING")

            #SERVER -> BOT
            #print("SERVER ->",end="")
            #data = input()#lbRecv(sock, recvbuffer)
            data = lbRecv(sock, recvbuffer)
            #print(data)
            if DEBUG:
                print(data)
            else:
                if not dontGiveBot(data):
                    print(data, file=proc.stdin, flush=True)
            updateViz(viz,vizbuffer,waterbuffer,data)

            testEnd(data)


            playerDead = playerDead or testDead(data)
            respond = isRequest(data)

            if respond and not playerDead:
                #print("I need a response now")
                #BOT -> SERVER
                bot_resp = input() if DEBUG else proc.stdout.readline().rstrip("\n")
                #print("> :", bot_resp)
                sayToServer(bot_resp)


    except gameEnded:
        finalWater(viz, waterbuffer)
        pass
    except BrokenPipeError:
        print("[-] Bot crashed (pipe broken)")

            
    print("[*] Link stopped")


import random
def readConfig(configfile):
    try:
        parser = configparser.ConfigParser()

        res = parser.read("./{}".format(configfile))

        if not res:
            print("[-] Config file \"{}\" could not be found".format(configfile))
            exit()

        #Ensure KeyErrors instead of fallback values for booleans
        parser['TEAM']['RandPostFixNr']
        parser['VISUALISER']['EnableVisualiser']
        parser['BOT']['PrintBotStdErr']

        teamname      = parser['TEAM']['TeamName']
        postfixnr     = parser['TEAM'].getboolean('RandPostFixNr')
        viz           = parser['VISUALISER'].getboolean('EnableVisualiser')
        debug         = parser['BOT'].getboolean('PrintBotStdErr')
        runcommand    = parser['BOT']['RunCommand']
        (server,port) = parser['SERVER']['ServerAddress'].split(":")

        return (teamname+("("+str(random.randrange(99))+")" if postfixnr else ""), viz, debug, runcommand, server, port)

    except Exception as e:
        print("[-] Error parsing the config file:\n\t{}\n\t{}".format(e.__class__.__name__, e))
        exit()


def work():
    global proc, sock, debugfile, team

    parser = ArgumentParser()
    parser.add_argument("altconfig", nargs='?', default="config")
    args = parser.parse_args()

    print("[+] Starting client")
    (team, viz_enabled, debug_on, command, server, port) = readConfig(args.altconfig)

    print(team)

    proc = Popen(command, shell=SHELLMODE, stdin=PIPE, stdout=PIPE, stderr=PIPE if debug_on else DEVNULL, bufsize=1, universal_newlines=True, preexec_fn=os.setsid if os.name == "posix" else None)

    if debug_on:
        stderr_start = Event()
        stderr_thread = Thread(target=print_stderr, args=(proc.stderr, stderr_start))
        stderr_thread.daemon = True # thread dies with the program
        stderr_thread.start()


    print("[?] Enter room key:\n> ",end="")
    roomkey = input().strip()

    establish_connection(server, port, team, roomkey)

    otherteam = waitForChallenge()

    print("[+] Challenged by {}".format(otherteam))

    viz = None
    #Move to separate function
    if viz_enabled:
        try:
            viz = VisualiserWrapper(Visualiser(True,1))
            print("[+] UI running")
        except Exception as e:
            print("[-] Got an error:")
            print(e)
            print(proc.stderr.read(), end="")
    else:
        viz = VisualiserWrapper(None)

    print("READY")
    sayToServer("READY")

    if debug_on:
        print("[*] Enabling bot StdErr output")
        stderr_start.set()
    
    becomeLink(viz=viz)
    try:
        time.sleep(5)#Should maybe be an option?
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
