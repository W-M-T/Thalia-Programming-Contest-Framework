#!/usr/bin/python3

from subprocess import Popen, PIPE, STDOUT
import os
import signal
import socket
import time
import select
from Visualiser import Visualiser

proc = None
sock = None
linebuffer = []
SHELLMODE = True
RECVCONST = 4096

#TODO:
# line buffer de socket receive in zowel client als server
# synchronizeer op de lobby in de server waarbij een nieuwe connectionhandler thread checkt of de room al voorkomt en zo ja
# de client van de andere connhandler jat en laat termineren via een flag
# die zit namelijk in een loop van poll-wait-check of nog niet gejat-poll
# de stelende connhandler start een gamerunner met beide clients en termineert zelf daarna
# zorg ook dat de gamerunner nooit nog poll responses hoeft te verwerken door een poll atomair te maken.

def cleanup():
    if not SHELLMODE and proc is not None:
        proc.kill()
    if proc is not None:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)


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
        data = sock.recv(RECVCONST).decode("utf-8").rstrip("\n").split("\n")
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

    s = sock.recv(RECVCONST)
    if s == s:
        pass

def readConfig():
    with open("./config","r") as conf:
        s = conf.read().split("\n")
        s = list(filter(lambda x: not (x.isspace() or x == ""), s))
        s = [x.strip() for x in s]
        try:
            teamname      = s[s.index("# TEAM NAME:") + 1]
            viz           = s[s.index("# VISUALISER ENABLED:") + 1] == "1"
            runcommand    = s[s.index("# BOT RUNNING COMMAND:") + 1]
            (server,port) = s[s.index("# SERVER ADDRESS:") + 1].split(":")
            return (teamname, viz, runcommand,server,port)

        except (ValueError, IndexError):
            print("[-] Config file could not be read")
            exit()

def work():
    global proc, sock

    print("[+] Starting client")
    (team,viz_enabled,command,server,port) = readConfig()

    proc = Popen(command, shell=SHELLMODE, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=1, universal_newlines=True, preexec_fn=os.setsid)

    #Test if an error occurred during startup (hacky)
    time.sleep(0.2)
    if not select.select([proc.stderr], [], [], 0)[0]:
        print("[+] Starting bot")
    else:
        print("[-] Got an error:")
        print(proc.stderr.read(), end="")
        exit()

    print("[?] Enter room key:\n> ",end="")
    roomkey = input().strip()

    establish_connection(server, port, team, roomkey)

    #waitForChallenge()

    #Move to battle start code
    if viz_enabled:
        try:
            viz = Visualiser(1,True,False)
            print("[+] UI running")
        except Exception as e:
            print("[-] Got an error:")
            print(e)
            print(proc.stderr.read(), end="")



    
    

def main():
    try:
        work()
    except KeyboardInterrupt:
        print("\n[-] Force terminated")

if __name__ == "__main__":
    main()