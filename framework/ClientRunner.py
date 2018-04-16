#!/usr/bin/python3

from subprocess import Popen, PIPE, STDOUT
import os
import signal
import socket
import time
import select


proc = None
sock = None
linebuffer = []
SHELLMODE = True
RECVCONST = 4096

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

    while True:
        print("WAITING")
        s = lbrecv()
        if s.find("PING") == 0:
            print("PONG")
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

def becomeLink(viz):
    global proc, sock
    
    end = False

    while not end:
        print("LOOPING")

        #SERVER -> BOT
        data = lbrecv()
        print(data)
        print(data, file=proc.stdin, flush=True)

        flow = getDepth(data)

        if flow >= 2:
            #BOT -> SERVER
            bot_resp = proc.stdout.readline().rstrip("\n")
            print(bot_resp)
            sayToServer(bot_resp)

        if flow >= 3:
            #SERVER -> BOT AGAIN
            data_result = lbrecv()
            print(data_result)
            print(data, file=prod.stdin, flush=True)

            if data.find("GAME RESULT ") == 0:
                print("GAME OVER")
                end = True
    print("Link stopped")


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
    (team,viz_enabled, debug_on, command,server,port) = readConfig()
    print(team)

    if debug_on:
        debugfile = open("./stderr.txt","w")
    proc = Popen(command, shell=SHELLMODE, stdin=PIPE, stdout=PIPE, stderr=debugfile if debug_on else DEVNULL, bufsize=1, universal_newlines=True, preexec_fn=os.setsid)

    #Test if an error occurred during startup (hacky)
    '''
    time.sleep(0.2)
    if not select.select([proc.stderr], [], [], 0)[0]:
        print("[+] Starting bot")
    else:
        print("[-] Got an error:")
        print(proc.stderr.read(), end="")
        exit()
    '''

    print("[?] Enter room key:\n> ",end="")
    roomkey = input().strip()

    establish_connection(server, port, team, roomkey)

    otherteam = waitForChallenge()

    #Move to battle start code
    if viz_enabled:
        try:
            from Visualiser import Visualiser
            viz = Visualiser(1,True,False)
            viz.placeShip(True,(1,1), (1,5))
            viz.placeShip(False,(2,2), (4,2))
            import random
            for i in range(4):
                viz.change(True,(random.randrange(0,10),random.randrange(0,10)),viz.ISLAND)
            print("[+] UI running")
        except Exception as e:
            print("[-] Got an error:")
            print(e)
            print(proc.stderr.read(), end="")

    sayToServer("READY")
    
    becomeLink(viz)

    print("[*] Client ended")


    
    

def main():
    try:
        work()
    except KeyboardInterrupt:
        print("\n[-] Force terminated")

if __name__ == "__main__":
    main()