#!/usr/bin/env python3

from subprocess import Popen, PIPE, STDOUT, DEVNULL
import os
import signal
import socket
import time
import select
from argparse import ArgumentParser
import configparser
from Util import lbRecv, stripFormat, parseCoord, sockSend, RecvBuffer
from Visualiser import Visualiser, VisualiserWrapper

#refactor:
#move the parsing and viz update code to another file to keep this runner independent of the game

proc = None
sock = None
recvbuffer = RecvBuffer()
SHELLMODE = True

DEBUG = True
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


def sayToServer(data):
    global sock

    sockSend(sock, data)


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


def testEnd(data):
    if data.find("GAME RESULT ") == 0:
        print("GAME OVER:",data)
        raise gameEnded

def isRequest(data):
    return data.find("REQUEST MOVE") == 0


def updateViz(viz,data,response=None): #No parsing error handling for server data (has to be correct as a part of the framework)
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

def becomeLink(viz):
    global proc, sock
    
    try:

        while True:
            #print("LOOPING")

            #SERVER -> BOT
            data = lbRecv(sock, recvbuffer)
            if DEBUG:
                print(data)
            else:
                print(data, file=proc.stdin, flush=True)
            updateViz(viz,data)

            testEnd(data)

            respond = isRequest(data)

            if respond:
                #BOT -> SERVER
                bot_resp = input() if DEBUG else proc.stdout.readline().rstrip("\n")
                print(bot_resp)
                sayToServer(bot_resp)
                updateViz(viz,data,response=bot_resp)

                testEnd(data)

    except gameEnded:
        pass

            
    print("Link stopped")


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
        parser['BOT']['WriteStdErrToFile']

        teamname      = parser['TEAM']['TeamName']
        postfixnr     = parser['TEAM'].getboolean('RandPostFixNr')
        viz           = parser['VISUALISER'].getboolean('EnableVisualiser')
        debug         = parser['BOT'].getboolean('WriteStdErrToFile')
        debugfile     = parser['BOT']['StdErrFile']
        runcommand    = parser['BOT']['RunCommand']
        (server,port) = parser['SERVER']['ServerAddress'].split(":")

        return (teamname+("("+str(random.randrange(99))+")" if postfixnr else ""), viz, debug, debugfile, runcommand, server, port)

    except Exception as e:
        print("[-] Error parsing the config file:\n\t{}\n\t{}".format(e.__class__.__name__, e))
        exit()


def work():
    global proc, sock, debugfile, team

    parser = ArgumentParser()
    parser.add_argument("altconfig", nargs='?', default="config")
    args = parser.parse_args()

    print("[+] Starting client")
    (team, viz_enabled, debug_on, debug_file, command, server, port) = readConfig(args.altconfig)

    print(team)

    if debug_on:
        debugfile = open(debug_file,"w")
        #Write initial line containing time
    proc = Popen(command, shell=SHELLMODE, stdin=PIPE, stdout=PIPE, stderr=debugfile if debug_on else DEVNULL, bufsize=1, universal_newlines=True, preexec_fn=os.setsid)

    print("[?] Enter room key:\n> ",end="")
    roomkey = input().strip()

    establish_connection(server, port, team, roomkey)

    otherteam = waitForChallenge()

    print("[+] Challenged by {}".format(otherteam))

    #Move to separate function
    if viz_enabled:
        try:
            viz = VisualiserWrapper(Visualiser(True,1))
            #viz.updateTitle("You ({})".format(team),"Other ({})".format(otherteam))

            print("[+] UI running")
        except Exception as e:
            print("[-] Got an error:")
            print(e)
            print(proc.stderr.read(), end="")
    else:
        viz = VisualiserWrapper(None)

    print("READY")
    sayToServer("READY")
    
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