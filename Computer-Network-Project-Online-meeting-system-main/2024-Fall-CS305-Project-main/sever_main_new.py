import socket
import threading
import json
from queue import Queue

# Server Configuration
IP = '127.0.0.1'
PORT = 8087
BUFLEN = 1024

# Global Variables
clients = {}  # Stores connected clients {username: (socket, address)}
meetings = {}  # Stores meetings {conference_id: [username1, username2, ...]}
lock = threading.Lock()

class ServerMain:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[Server] Started on {self.host}:{self.port}")

    def broadcast(self, message, exclude_user=None):
        """Send a message to all connected clients except the excluded user."""
        with lock:
            for username, (client_socket, _) in clients.items():
                if username != exclude_user:
                    try:
                        client_socket.send(message.encode())
                    except:
                        print(f"[Error] Failed to send message to {username}")

    def handle_client(self, client_socket, address):
        """Handle communication with a connected client."""
        username = None
        try:
            while True:
                data = client_socket.recv(BUFLEN).decode()
                if not data:
                    break

                request = json.loads(data)
                action = request.get("action")

                if action == "login":
                    username = request.get("username")
                    with lock:
                        if username not in clients:
                            clients[username] = (client_socket, address)
                            response = {"status": "success", "message": "Login successful."}
                            print(f"[Info] {username} logged in from {address}")
                        else:
                            response = {"status": "error", "message": "Username already taken."}
                    client_socket.send(json.dumps(response).encode())

                elif action == "create_conference":
                    conference_id = request.get("conference_id")
                    with lock:
                        if conference_id not in meetings:
                            meetings[conference_id] = [username]
                            response = {"status": "success", "conference_id": conference_id}
                            print(f"[Info] Conference {conference_id} created by {username}")
                        else:
                            response = {"status": "error", "message": "Conference ID already exists."}
                    client_socket.send(json.dumps(response).encode())

                elif action == "join_conference":
                    conference_id = request.get("conference_id")
                    with lock:
                        if conference_id in meetings:
                            if username not in meetings[conference_id]:
                                meetings[conference_id].append(username)
                            response = {"status": "success", "conference_id": conference_id}
                            print(f"[Info] {username} joined conference {conference_id}")
                        else:
                            response = {"status": "error", "message": "Conference not found."}
                    client_socket.send(json.dumps(response).encode())

                elif action == "quit_conference":
                    conference_id = request.get("conference_id")
                    with lock:
                        if conference_id in meetings and username in meetings[conference_id]:
                            meetings[conference_id].remove(username)
                            response = {"status": "success"}
                            print(f"[Info] {username} left conference {conference_id}")
                        else:
                            response = {"status": "error", "message": "You are not in this conference."}
                    client_socket.send(json.dumps(response).encode())

                elif action == "cancel_conference":
                    conference_id = request.get("conference_id")
                    with lock:
                        if conference_id in meetings and username in meetings[conference_id]:
                            del meetings[conference_id]
                            response = {"status": "success"}
                            print(f"[Info] {username} canceled conference {conference_id}")
                        else:
                            response = {"status": "error", "message": "You cannot cancel this conference."}
                    client_socket.send(json.dumps(response).encode())

        except Exception as e:
            print(f"[Error] Exception occurred with {username}: {e}")
        finally:
            if username:
                with lock:
                    clients.pop(username, None)
                print(f"[Info] {username} disconnected")
            client_socket.close()

    def start(self):
        while True:
            client_socket, address = self.server_socket.accept()
            print(f"[Connection] New connection from {address}")
            threading.Thread(target=self.handle_client, args=(client_socket, address)).start()

if __name__ == "__main__":
    server = ServerMain(IP, PORT)
    server.start()
