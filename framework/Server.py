#!/usr/bin/python3

import socket as s
from Game import GameRunner
from threading import Thread, Lock
from threading import enumerate
from enum import IntEnum
from time import sleep
from Visualiser import Visualiser
from argparse import ArgumentParser


incomingsocket = None
LISTENPORT = 42000
RECVCONST = 4096
viz = None


def cleanup():
    if incomingsocket is not None:
        incomingsocket.close()
        print("[-] Shut down abnormally")

import atexit
atexit.register(cleanup)


lobby = {}
lobbyLock = Lock()



def stripFormat(form,data):
    if data.find(form) == 0:
        return data.replace(form,"",1)
    else:
        return None

def poll(connection):
    try:
        connection.settimeout(2)
        connection.send(("PING\n").encode("utf-8"))
        #Do nonbuffered receive
        bytedata = connection.recv(RECVCONST)
        if len(bytedata) == 0:#Connection was closed
            return False
        connection.settimeout(None)
        return True
    except Exception as e:
        print("!!!!!",e)
        connection.settimeout(None)
        return False


class ConnHandler(Thread):

    def __init__(self, connection, client):
        super(ConnHandler, self).__init__(daemon=True)
        self.connection = connection
        self.client = client
        self.linebuffer = []


    def lbrecv(self):#Line buffered receive
        #unhandled case is if the socket receive ends in the middle of a message, wich should only happen if there are more than 4096 bytes in the receive buffer
        if self.linebuffer:
            return self.linebuffer.pop(0)
        else:
            bytedata = self.connection.recv(RECVCONST)
            if len(bytedata) == 0:#Connection was closed
                raise s.timeout
            data = bytedata.decode("utf-8").rstrip("\n").split("\n")#maybe catch the possible decode error?
            ret = data.pop(0)
            self.linebuffer.extend(data)
            return ret

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
                (foundConn, foundLock) = lobby[self.key]
                lobbyLock.release()#Now we know that the current index cannot be removed/modified while we are working, because we have the index lock
                other_alive = poll(foundConn["socket"])

                if other_alive:
                    print("Starting match in room \"{}\"".format(self.key))
                    #Start game runner thread
                    gr = GameRunner({"name":self.name,"socket":self.connection,"addr":self.client},foundConn, viz = viz)#Do some test to find out
                    gr.start()
                    #Delete this index
                    lobbyLock.acquire()
                    del(lobby[self.key])#We know that it still exists, because to delete it you need the index lock
                    lobbyLock.release()
                    indexLock.release()#Let the other connhandlers for this index work
                else:
                    print("Unzombified room \"{}\" with {}:{} ({})".format(self.key, *self.client, self.name))
                    #Replace the dead connection
                    foundConn["socket"].close()
                    lobbyLock.acquire()
                    lobby[self.key] = ({"name":self.name,"socket":self.connection,"addr":self.client},indexLock)
                    lobbyLock.release()
                    indexLock.release()

            else:
                print("Recreated room \"{}\" for {}:{} ({})".format(self.key, *self.client, self.name))
                #Match was started in the meantime + lobby room is empty
                #Add key, copy index lock (so new threads enter the same line)
                lobby[self.key] = ({"name":self.name,"socket":self.connection,"addr":self.client},indexLock)
                lobbyLock.release()
                #release index lock to free any threads later in line
                indexLock.release()


        else:
            #Add key, create index lock and end
            print("Creating new room \"{}\" for {}:{} ({})".format(self.key, *self.client, self.name))
            lobby[self.key] = ({"name":self.name,"socket":self.connection,"addr":self.client},Lock())
            lobbyLock.release()


    def run(self): 
        try:
            #Get client info
            self.connection.settimeout(2)
            self.name = stripFormat("CLIENT NAME ", self.lbrecv())
            self.key = stripFormat("CLIENT KEY ", self.lbrecv())

            if self.name is None or self.key is None:
                raise Exception("[-] Protocol not followed by {}:{}".format(*self.client))
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

        except KeyboardInterrupt:#Only ever happens if serve is called from the main thread
            #print(enumerate())
            incomingsocket.close()
            incomingsocket = None
            print("\r[+] Shutting down")
        

    def run(self):
        Server.serve()

def main():
    global incomingsocket, viz
    
    parser = ArgumentParser(description="Programming contest framework")
    parser.add_argument("-v", "--visual", action="store_true", help="Enable visualiser")
    args = parser.parse_args()

    server = Server(True)
    #Server.serve()
    server.start()

    try:
        if args.visual:
            viz = Visualiser(1,True,True, is_main=False)
            viz.doUIThread()#Necessary because TKinter needs the main thread in order not to complain
        else:
            server.join()
    except KeyboardInterrupt:
        incomingsocket.close()
        incomingsocket = None
        print("\r[+] Shutting down")
        

if __name__ == "__main__":
    main()