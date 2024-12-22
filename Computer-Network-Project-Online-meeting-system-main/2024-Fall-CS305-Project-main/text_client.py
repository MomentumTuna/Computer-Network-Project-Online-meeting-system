import socket
import threading
from datetime import datetime

# Client Code
class VideoMeetingClient:
    def __init__(self, name, host='127.0.0.1', port=12345):
        self.name = name
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_to_server(self):
        self.client_socket.connect((self.host, self.port))
        threading.Thread(target=self.receive_messages).start()

    def send_message(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        full_message = f"[{timestamp}] {self.name}: {message}"
        self.client_socket.send(full_message.encode('utf-8'))
        full_message = f"*[{timestamp}] I: {message}"
        print(full_message)

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                print(message)
            except:
                print("Disconnected from server.")
                self.client_socket.close()
                break
              

if __name__ == "__main__":
    client_name = input("Enter your name: ")
    client = VideoMeetingClient(name=client_name)
    client.connect_to_server()
    print(f"Welcome, {client_name}!")
    while True:
        message = input()
        client.send_message(message)