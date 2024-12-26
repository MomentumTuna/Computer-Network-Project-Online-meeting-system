import socket
import time
import tkinter
from tkinter import messagebox, scrolledtext
import threading
from util import *
import json

conference_id = ''

class ClientMain:
    def __init__(self, user='', host='127.0.0.1', port=12345):
        self.user = user
        self.serverIP = ''
        self.serverPort = 0
        self.conference_id = ''
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def send_request(self, request):
            '''
                通用方法：向服务器发送请求并接受应答
            '''
            try:
                request = json.dumps(request)
                self.client_socket.send(request.encode('utf-8'))
                response = self.client_socket.recv(1024)
                response = json.loads(response.decode())
                return response
            except Exception as e:
                print(f"[Error] Failed to send request: {e}")
                return None
            
    def connect_to_server(self):
        self.client_socket.connect((self.serverIP, self.serverPort))
        request = {"action":"register","username": self.user}
        print(type(request),request)
        response = self.send_request(request)
        if response.get and response.get("status") == "success":
            print("Successfully registered into the server")
        #threading.Thread(target=self.)
        
    def create_conference(self):
        request = {"action": "create_conference"}
        response = self.send_request(request)
        if response and response.get("status") == "success":
            self.conference_id = response.get("conference_id")
            self.on_meeting = True
            print(f"[Info] Conference created successfully! ID: {self.conference_id}")
        else:
            print("[Error] Failed to create conference.")
        
    def join_conference(self,conference_id):
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

        request = json.dumps({"action": "quit_conference", "conference_id": self.conference_id})
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

        request = json.dumps({"action": "cancel_conference", "conference_id": self.conference_id})
        response = self.send_request(request)
        if response and response.get("status") == "success":
            self.on_meeting = False
            self.conference_id = None
            print("[Info] Conference canceled successfully.")
        else:
            print("[Error] Failed to cancel the conference.")
    
    def onClick_join_conf(self):
        global conference_id
        input_ui = tkinter.Tk()
        input_ui.geometry("600x375+300+100")  
        label_conf_id = tkinter.Label(input_ui,text="Conference ID: ")
        label_conf_id.place(x=200,y=120,width=150,height=50)
        entry_conf_id = tkinter.Entry(input_ui, width=100, textvariable=self.conference_id)
        entry_conf_id.place(x=330,y=125,width=200,height=25)
        enterButton = tkinter.Button(input_ui, text="Enter", command=lambda: self.onClick_join_enter(input_ui, entry_conf_id))
        enterButton.place(x=250, y=200, width=80, height=50)
        
        
    def onClick_join_enter(self,input_ui,entry_conf_id):
        self.join_conference(conference_id)
        while True:
            if self.conference_id:
                input_ui.destroy()
                break
            else:
                continue
            
    def init_login_window(self):
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

        loginButton = tkinter.Button(root0, text="登录", command=lambda: self.Login(root0, entryIP, entryPORT, entryUSER))
        loginButton.place(x=175, y=150, width=40, height=25)
        root0.bind('<Return>', lambda event: self.Login(root0, entryIP, entryPORT, entryUSER))
        root0.mainloop()
        return root0,entryIP,entryPORT,entryUSER
    
    def Login(self, root0,entryIP,entryPORT,entryUSER):
        self.serverIP = entryIP.get()
        self.serverPort = int(entryPORT.get())
        self.user = entryUSER.get()
        if not self.serverIP:
            tkinter.messagebox.showwarning('warning', message='WrongIP!')
        elif not self.serverPort:
            tkinter.messagebox.showwarning('warning', message='WrongPort!')
        else:
            root0.destroy()

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

        tkinter.Button(client_ui, text="create",command=self.create_conference).pack(side='left', anchor='n', padx=10, pady=10)
        tkinter.Button(client_ui, text="quit",command=self.quit_conference).pack(side='left', anchor='n', padx=10, pady=10)
        tkinter.Button(client_ui, text="join",command=self.onClick_join_conf).pack(side='left', anchor='n', padx=10, pady=10)
        tkinter.Button(client_ui, text="cancel",command=self.cancel_conference).pack(side='left', anchor='n', padx=10, pady=10)
        #tkinter.Button(client_ui, text="switch").pack(side='left', anchor='n', padx=10, pady=10)
        # Talking part
        listbox = tkinter.scrolledtext.ScrolledText(client_ui)
        listbox.place(x=775, y=25, width=350, height=500)
        listbox.tag_config('tag1', foreground='blue', backgroun="white")
        listbox.insert(tkinter.END, 'Welcome ' + self.user + ' join!', 'tag1')
        listbox.insert(tkinter.END, '\n')

        # Talking-Entry
        INPUT = tkinter.StringVar()
        INPUT.set('')
        entryInput = tkinter.Entry(client_ui, width=120, textvariable=INPUT)
        entryInput.place(x=775, y=550, width=350, height=100)

        def send_message():
            message = entryInput.get()
            socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(message.encode(), (IP, int(PORT)))
            print("send message:", message)
            print("\nto : "+self.serverIP+"; "+self.serverPort+"\n")
            INPUT.set('')
            return 'break'

        but_send = tkinter.Button(client_ui, text="SEND",command=send_message)
        but_send.place(x=1050, y=660, width=75, height=50)
        
        self.client_ui = client_ui
        client_ui.mainloop()
        
        

if __name__ == "__main__":
    client = ClientMain()
    client.init_login_window()
    client.connect_to_server()
    client.open_ui()


