from socket import *
import time
import tkinter
import threading
import json
# from util import *

IP = '127.0.0.1'
SERVER_PORT = 50000
user = ''
listbox1 = ''
show = 1
users = []
chat = '0'
chat_pri = ''

# 登录_Part
root0 = tkinter.Tk()
root0.geometry("450x225+300+100")
root0.title('Log in')
root0.resizable(0, 0)
one = tkinter.Label(root0, width=300, height=150)
one.pack()
IP = tkinter.StringVar()
IP.set('')
PORT = tkinter.StringVar()
PORT.set('')
USER = tkinter.StringVar()
USER.set('')

labelIP = tkinter.Label(root0, text='Server_IP')
labelIP.place(x=120, y=5, width=100, height=40)
entryIP = tkinter.Entry(root0, width=60, textvariable=IP)
entryIP.place(x=220, y=10, width=100, height=30)

labelPORT = tkinter.Label(root0, text='Server_Port')
labelPORT.place(x=120, y=40, width=100, height=40)
entryPORT = tkinter.Entry(root0, width=60, textvariable=PORT)
entryPORT.place(x=220, y=45, width=100, height=30)

labelUSER = tkinter.Label(root0, text='Username')
labelUSER.place(x=120, y=75, width=100, height=40)
entryUSER = tkinter.Entry(root0, width=60, textvariable=USER)
entryUSER.place(x=220, y=80, width=100, height=30)


def Login():
    global IP, PORT, user
    IP = entryIP.get()
    PORT = entryPORT.get()
    user = entryUSER.get()
    if not IP:
        tkinter.messagebox.showwarning('warning', message='WrongIP!')
    elif not PORT:
        tkinter.messagebox.showwarning('warning', message='WrongPort!')
    else:
        root0.destroy()


    

loginButton = tkinter.Button(root0, text="登录", command=Login)
loginButton.place(x=175, y=150, width=40, height=25)
root0.bind('<Return>', Login)

root0.mainloop()


ip_port = (IP, int(PORT))
s = socket(AF_INET, SOCK_DGRAM)
if user:
    s.sendto(user.encode(), ip_port)
else:
    s.sendto('用户名不存在', ip_port)
    user = IP + ':' + PORT

# 界面_Part
client_ui = tkinter.Tk()
client_ui.title("Meeting-Client-Part")
client_ui.geometry("1200x750+300+100")

tkinter.Button(client_ui, text="create").pack(side='left', anchor='n', padx=10, pady=10)
tkinter.Button(client_ui, text="quit").pack(side='left', anchor='n', padx=10, pady=10)
tkinter.Button(client_ui, text="join").pack(side='left', anchor='n', padx=10, pady=10)
tkinter.Button(client_ui, text="cancel").pack(side='left', anchor='n', padx=10, pady=10)
tkinter.Button(client_ui, text="switch").pack(side='left', anchor='n', padx=10, pady=10)

client_ui.mainloop()


class ClientMain:
    def __init__(self, name, host='127.0.0.1', port=12345):
        self.name = name
        self.host = host
        self.port = port
        self.client_socket = socket(AF_INET, SOCK_STREAM)

    def connect_to_server(self):
        self.client_socket.connect((self.host, self.port))
        #threading.Thread(target=self.)
        
    def send_request(self, request):
        '''
            通用方法：向服务器发送请求并接受应答
        '''
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(self.server_addr)
                sock.sendall(request.encode())
                response = sock.recv(1024).decode()
                return response
        except Exception as e:
            print(f"[Error] Failed to send request: {e}")
            return None
        
    def create_conference(self):
        request = {"action": "create_conference"}
        response = self.send_request(request)
        if response and response.get("status") == "success":
            self.conference_id = response.get("conference_id")
            self.on_meeting = True
            print(f"[Info] Conference created successfully! ID: {self.conference_id}")
        else:
            print("[Error] Failed to create conference.")
        
    def join_conference(self, conference_id):
        request = {"action": "join_conference", "conference_id": conference_id}
        response = self.send_request(request)
        if response and response.get("status") == "success":
            self.conference_id = conference_id
            self.on_meeting = True
            print(f"[Info] Joined conference {conference_id} successfully!")
        else:
            print("[Error] Failed to join conference.")
    
    def quit_conference(self):
        if not self.on_meeting:
            print("[Warn] You are not in any conference.")
            return

        request = {"action": "quit_conference", "conference_id": self.conference_id}
        response = self.send_request(request)
        if response and response.get("status") == "success":
            self.on_meeting = False
            self.conference_id = None
            print("[Info] Successfully quit the conference.")
        else:
            print("[Error] Failed to quit the conference.")

    def cancel_conference(self):
        """
        取消会议：当用户是会议管理员时调用
        """
        if not self.on_meeting:
            print("[Warn] You are not in any conference.")
            return

        request = {"action": "cancel_conference", "conference_id": self.conference_id}
        response = self.send_request(request)
        if response and response.get("status") == "success":
            self.on_meeting = False
            self.conference_id = None
            print("[Info] Conference canceled successfully.")
        else:
            print("[Error] Failed to cancel the conference.")
    
    
    
    def open_ui(self):
        """
        part UI
        """
        client_ui = tkinter.Tk()
        client_ui.title("Meeting-Client-Part")
        client_ui.geometry("1200x750+300+100")
        """
        client_ui.minsize(600, 375)
        client_ui.maxsize(1200, 750)
        tkinter.Label(client_ui, text="Name:").pack(anchor='w', padx=400, pady=250)
        name_entry = tkinter.Entry(client_ui)
        name_entry.pack(padx=10, pady=5)
        """

        tkinter.Button(client_ui, text="create").pack(side='left', anchor='n', padx=10, pady=10)
        tkinter.Button(client_ui, text="quit").pack(side='left', anchor='n', padx=10, pady=10)
        tkinter.Button(client_ui, text="join").pack(side='left', anchor='n', padx=10, pady=10)
        tkinter.Button(client_ui, text="cancel").pack(side='left', anchor='n', padx=10, pady=10)
        tkinter.Button(client_ui, text="switch").pack(side='left', anchor='n', padx=10, pady=10)

        self.client_ui = client_ui
        client_ui.mainloop()


if __name__ == "__main__":
    
    client_name = input("Enter your name: ")
    client = ClientMain(client_name)


