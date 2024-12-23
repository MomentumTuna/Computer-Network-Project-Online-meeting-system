import tkinter
from socket import *
import threading
import queue
import json
import os
import sys

# define
IP = '127.0.0.1'
#IP = '192.168.1.103'
PORT = 8087
messages = queue.Queue()
users = []
lock = threading.Lock()
BUFLEN=512

def Current_users():
    current_suers = []
    for i in range(len(users)):
        current_suers.append(users[i][0])      #store user name
    return  current_suers

class ServerMain:
    global users, que, lock

    def __init__(self):
        threading.Thread.__init__(self)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    def receive(self):
        while True:
            print('a')
            Info, addr = self.s.recvfrom(1024)
            print('b')
            Info_str = str(Info, 'utf-8')
            userIP = addr[0]
            userPort = addr[1]
            print(f'Info_str:{Info_str},addr:{addr}')
            if '~0' in Info_str:  # 群聊
                data = Info_str.split('~')
                print("data_after_slpit:", data)  # data_after_slpit: ['cccc', 'a', '0']
                message = data[0]  # data
                userName = data[1]  # name
                chatwith = data[2]  # 0
                message = userName + '~' + message + '~' + chatwith  # 界面输出用户格式
                print("message:", message)
                self.Load(message, addr)
            elif '~' in Info_str and '0' not in Info_str:
                data = Info_str.split('~')
                print("data_after_slpit:", data)
                message = data[0]
                userName = data[1]
                chatwith = data[2]
                message = userName + '~' + message + '~' + chatwith
                self.Load(message, addr)
            else:
                tag = 1
                temp = Info_str
                for i in range(len(users)):
                    if users[i][0] == Info_str:
                        tag = tag + 1
                        Info_str = temp + str(tag)
                users.append((Info_str, userIP, userPort))
                print("users:", users)
                Info_str = Current_users()
                print("USERS:", Info_str)
                self.Load(Info_str, addr)



