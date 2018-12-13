#!/usr/bin/env python3

import socket as s
from Game import GameRunner
from threading import Thread, Lock
from enum import IntEnum
from time import sleep
from Visualiser import Visualiser
from argparse import ArgumentParser
from Util import lbRecv, stripFormat, sockSend, RecvBuffer


incomingsocket = None
LISTENPORT = 42042
viz = None
RECVCONST = 4096

def cleanup():
    if incomingsocket is not None:
        incomingsocket.close()
        print("[-] Shut down abnormally")

import atexit
atexit.register(cleanup)


lobby_size = 2

lobby = {}
lobbyLock = Lock()

spectators = {}
#Not syncronized because this feature is a quick hack (fix later). Not necessary to fix when there is just one spectator.

def poll_mult(foundlobby):#TODO only poll a lobby when the amount of found connections is such that a game would start if everyone were alive
    live = []
    dead = []
    for u in foundlobby:#Currently sequential. Would be faster in parallel.
        if poll(u["socket"]):
            live.append(u)
        else:
            dead.append(u)
    return (live,dead)

def poll(connection):
    try:
        connection.settimeout(2)
        sockSend(connection, "PING")
        #Do nonbuffered receive
        bytedata = connection.recv(RECVCONST)
        if len(bytedata) == 0:#Connection was closed
            return False
        connection.settimeout(None)
        return True
    except Exception as e:
        print("!!!!!",e.__class__.__name__, e)
        connection.settimeout(None)
        return False


class ConnHandler(Thread):

    def __init__(self, connection, client):
        super(ConnHandler, self).__init__(daemon=True)
        self.connection = connection
        self.client = client
        self.recvbuffer = RecvBuffer()

    def handleLobby(self):
        global viz

        lobbyLock.acquire()
        if self.key in lobby:
            indexLock = lobby[self.key][1]
            lobbyLock.release()#Prevents poll from blocking all rooms

            indexLock.acquire()
            lobbyLock.acquire()
            if self.key in lobby:
                #Lobby room not empty
                (foundConns, foundLock) = lobby[self.key]
                lobbyLock.release()#Now we know that the current index cannot be removed/modified while we are working, because we have the index lock
                (alives_lobby,deads_lobby) = poll_mult(foundConns)

                if len(alives_lobby)+1 == lobby_size:#Full lobby, time to start
                    print("Starting match in room \"{}\"".format(self.key))
                    #Check if there is a spectator waiting (still refactor this)
                    if self.key in spectators:
                        spec = spectators[self.key]
                        del(spectators[self.key])
                    else:
                        spec = None
                    #Start game runner thread
                    gr = GameRunner([*foundConns,{"name":self.name,"socket":self.connection,"addr":self.client}], viz = viz, spectator = spec)
                    gr.start()
                    #Delete this index
                    lobbyLock.acquire()
                    del(lobby[self.key])#We know that it still exists, because to delete it you need the index lock
                    lobbyLock.release()
                    indexLock.release()#Let the other connhandlers for this index work
                else:#Add this user to the lobby
                    print("Added to room \"{}\" for {}:{} ({})".format(self.key, *self.client, self.name))
                    print("Room \"{}\" now contains {}/{}:\n\t{}".format(self.key,
                                                                        len(alives_lobby)+1,
                                                                        lobby_size,
                                                                        "\n\t".join([self.name,*list(map(lambda x: x["name"], alives_lobby))])))
                    #Close dead/unresponsive connections
                    for dead in deads_lobby:
                        dead["socket"].close()
                    lobbyLock.acquire()
                    lobby[self.key] = ([*alives_lobby,{"name":self.name,"socket":self.connection,"addr":self.client}],indexLock)
                    lobbyLock.release()
                    indexLock.release()

            else:
                print("Recreated room \"{}\" for {}:{} ({})".format(self.key, *self.client, self.name))
                #Match was started in the meantime + lobby room is empty
                #Add key, copy index lock (so new threads enter the same line)
                lobby[self.key] = ([{"name":self.name,"socket":self.connection,"addr":self.client}],indexLock)
                lobbyLock.release()
                #release index lock to free any threads later in line
                indexLock.release()


        else:
            #Add key, create index lock and end
            #Maybe handle the case for lobby sizes of 1?
            print("Creating new room \"{}\" for {}:{} ({})".format(self.key, *self.client, self.name))
            lobby[self.key] = ([{"name":self.name,"socket":self.connection,"addr":self.client}],Lock())
            lobbyLock.release()


    def run(self): 
        try:
            #Get client info
            self.connection.settimeout(2)

            nameline = lbRecv(self.connection,self.recvbuffer)
            name = stripFormat("CLIENT NAME ", nameline)
            key = stripFormat("CLIENT KEY ", lbRecv(self.connection,self.recvbuffer))

            maybeSpectator = stripFormat("SPECTATOR",nameline)
            if maybeSpectator is not None and key is not None:
                print("[*] Incoming spectator for room \"{}\"".format(key))
                spectators[key] = self.connection
                return

            if name is None or key is None:
                raise Exception("[-] Protocol not followed by {}:{}".format(*self.client))
            self.name = name
            self.key = key
            self.connection.settimeout(None)
            print("[*] Incoming connection from {}:{} ({}) for room \"{}\"".format(*self.client, self.name, self.key))

            self.handleLobby()
        except s.timeout:
            print("Timed out during initial info: {}:{}".format(*self.client))


class Server(Thread):#Handle the keyboardinterrupt from the main thread still

    def __init__(self,daemon):
        super(Server, self).__init__(daemon=daemon)

    def serve():
        global incomingsocket

        incomingsocket = s.socket()
        local_addr = s.gethostbyname(s.gethostname())
        #local_addr = s.gethostname()
        print("[+] Starting server at", local_addr)
        incomingsocket.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)
        incomingsocket.bind(('',LISTENPORT))
        incomingsocket.listen()


        try:
            while True:
                (connection, client) = incomingsocket.accept()
                handler = ConnHandler(connection, client)
                handler.start()

                #Cull references to connection sockets so connections die when the gamerunner dies
                handler = None
                connection = None

        except KeyboardInterrupt:#Only ever happens if serve is called from the main thread
            #print(enumerate())
            incomingsocket.close()
            incomingsocket = None
            print("\r[+] Shutting down")
        

    def run(self):
        Server.serve()

def main():
    global incomingsocket, viz, lobby_size
    
    parser = ArgumentParser(description="Programming contest framework")
    parser.add_argument("-v", "--visual", action="store_true", help="Enable visualiser")
    parser.add_argument("-l", metavar="SIZE", default=2, type=int, help="Lobby size")
    args = parser.parse_args()

    lobby_size = args.l

    server = Server(True)
    #Server.serve()
    server.start()

    try:
        if args.visual:
            viz = Visualiser(True, 1)
            viz.doUIThread()
        else:
            server.join()
    except KeyboardInterrupt:
        incomingsocket.close()
        incomingsocket = None
        print("\r[+] Shutting down")
        

if __name__ == "__main__":
    main()