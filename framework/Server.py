#!/usr/bin/python3

import socket as s
from Game import GameRunner
from threading import Thread, Lock
from enum import IntEnum
from time import sleep
from Visualiser import Visualiser


incomingsocket = None
LISTENPORT = 42000
RECVCONST = 4096

POLL_INTERVAL = 30

def cleanup():
    if incomingsocket is not None:
        incomingsocket.close()
        print("[-] Shut down abnormally")

import atexit
atexit.register(cleanup)


lobby = {}
lobbyLock = Lock()



class ConnHandler(Thread):

    def __init__(self, connection, client):
        super(ConnHandler, self).__init__(daemon=True)
        self.connection = connection
        self.client = client
        self.linebuffer = []
        self.die = False

    def lbrecv(self):#Line buffered receive
        #unhandled case is if the socket receive ends in the middle of a message, wich should only happen if there are more than 4096 bytes in the receive buffer

        if self.linebuffer:
            return self.linebuffer.pop(0)
        else:
            bytedata = self.connection.recv(RECVCONST)
            if len(bytedata) == 0:#Connection was closed
                raise s.timeout
            data = bytedata.decode("utf-8").rstrip("\n").split("\n")
            ret = data.pop(0)
            self.linebuffer.extend(data)
            return ret
   
    def findOrAddToLobby(self):
        lobbyLock.acquire()
        if self.key not in lobby:
            #print("Added {} {} to lobby".format(self.name, self.key))
            lobby[self.key] = self
            lobbyLock.release()
        else:
            other = lobby[self.key]     
            other.die = True
            self.die  = True
            del(lobby[self.key])
            lobbyLock.release()

            #Safer to do this after releasing the lock
            gr = GameRunner({"name":self.name,"socket":self.connection,"addr":self.client},{"name":other.name,"socket":other.connection,"addr":other.client})
            gr.start()


    def removeSelfFromLobby(self):
        lobbyLock.acquire()
        del(lobby[self.key])
        lobbyLock.release()

    def poll(self):
        self.connection.send(("PING\n").encode("utf-8"))
        self.lbrecv() #Don't even check if it is PONG

    def run(self):
        
        try:
            self.connection.settimeout(2)
            self.name = stripFormat("CLIENT NAME ", self.lbrecv())
            self.key = stripFormat("CLIENT KEY ", self.lbrecv())

            if self.name is None or self.key is None:
                raise Exception("Protocol not followed by {}:{}".format(*self.client))
            self.connection.settimeout(None)
            print("[*] Incoming connection from {}:{} ({}) for room \"{}\"".format(*self.client, self.name, self.key))

            self.findOrAddToLobby()

            self.connection.settimeout(2)
            while not self.die:
                try:
                    sleep(POLL_INTERVAL)
                    self.poll()
                except s.timeout:
                    if not self.die:#Not synchronized, i.e. edge case (known shippable)
                        self.removeSelfFromLobby()
                        print("Polling timed out for {} {}".format(self.name, self.key))
                        self.die = True
                
        except Exception as e:
            print(self,e)
        self.connection.close()


def stripFormat(form,data):
    if data.find(form) == 0:
        return data.replace(form,"",1)
    else:
        return None


def serve():
    global incomingsocket

    incomingsocket = s.socket()
    local_addr = s.gethostbyname(s.gethostname())
    #local_addr = s.gethostname()
    print("[+] Starting server at", local_addr)
    incomingsocket.bind(('',LISTENPORT))
    incomingsocket.listen()


    try:
        while True:
            (connection, client) = incomingsocket.accept()
            handler = ConnHandler(connection, client)
            handler.start()

    except KeyboardInterrupt:
        pass
    incomingsocket.close()
    incomingsocket = None
    print("\r[+] Shutting down")

def main():
    serve()

if __name__ == "__main__":
    main()