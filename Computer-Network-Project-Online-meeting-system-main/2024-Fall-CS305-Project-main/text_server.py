import socket
import threading
from datetime import datetime

# Server Code
class VideoMeetingServer:
    def __init__(self, host='127.0.0.1', port=12345):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []  # List to store client connections

    def start_server(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server started on {self.host}:{self.port}")
        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"New connection from {client_address}")
            self.clients.append(client_socket)
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if message:
                    self.broadcast_message(message, client_socket)
            except:
                self.clients.remove(client_socket)
                client_socket.close()
                break

    def broadcast_message(self, message, sender_socket):
        with threading.Lock():  # Ensures thread-safe access to self.clients
            for client in self.clients:
                if client != sender_socket:
                    try:
                        client.send(message.encode('utf-8'))
                    except Exception as e:
                        print(f"Error sending message to {client}: {e}")
                        self.clients.remove(client)
                        client.close()
                    
if __name__ == '__main__':
  server = VideoMeetingServer()
  server.start_server()     