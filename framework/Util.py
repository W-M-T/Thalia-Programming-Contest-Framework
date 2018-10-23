#!/usr/bin/env python3

RECVCONST = 4096

#TODO handle the difference in exceptions

def lbRecv(socket, linebuffer):#Line buffered receive
    #unhandled case is if the socket receive ends in the middle of a message, wich should only happen if there are more than 4096 bytes in the receive buffer
    if linebuffer:
        return linebuffer.pop(0)
    else:
        bytedata = socket.recv(RECVCONST)
        if len(bytedata) == 0:#Connection was closed
            raise Exception("Connection was closed") #s.timeout
        data = bytedata.decode("utf-8").rstrip("\n").split("\n")#maybe catch the possible decode error?
        ret = data.pop(0)
        linebuffer.extend(data)
        return ret

def sockSend(socket, data):
    socket.send((data+"\n").encode("utf-8"))


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

'''
from ClientRunner
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
'''
'''
Spectator
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
'''
'''
GameRunner
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
'''