#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket as s
from threading import Thread
import json
import sys
import struct

#This class contains all slient settings
#- loads settings from file
#- saves settings to file
class ClientSetting:
    def __init__(self, fname = ""):
        self.nickname = 'Jimmy'
        self.server_ip = 'localhost'
        self.port = 9191
        #and so on

        if fname:
            self.load(fname)

    def load(self, fname):
        #TODO: implement settings loading
        pass


class Client:
    sock = s.socket(s.AF_INET, s.SOCK_STREAM)               #Creating up network socket

    def __init__(self, nickname='Jimmy', address='localhost', port=9191):

        self.setting = ClientSetting()
        self.setting.nickname = nickname
        self.setting.server_ip = address
        self.setting.port = port

        self.sock.connect((self.setting.server_ip, self.setting.port))

        thread = Thread(target=self.listen)
        thread.daemon = True
        thread.start()

    def listen(self):
        while True:
            data = self.recv()
            if not data:
                break
            raw_data = json.loads(data)
            print("[%s]: %s" % (raw_data["nickname"], raw_data["msg"]))
    
    def send(self, input_msg): #Message sending method
        msg_data = {"nickname": self.setting.nickname, "msg": input_msg}
        raw_data = json.dumps(msg_data, ensure_ascii=False).encode('utf-8')
        msg = struct.pack('>I', len(raw_data)) + raw_data
        self.sock.sendall(msg)
    
    def recv(self): #Message receiving method
        raw_msglen = self.recvall(4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        return self.recvall(msglen)

    def recvall(self, n): #Вспомогательный метод для принятия сообщений, читает из сокета
        data = b''
        while len(data) < n:
            packet = self.sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def start(self):
        pass


if __name__ == "__main__":
    if len(sys.argv) > 1:
        clt = Client(sys.argv[1], 'localhost', 9191)
