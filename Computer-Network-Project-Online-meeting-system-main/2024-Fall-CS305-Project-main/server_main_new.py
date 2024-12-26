import socket
import threading
import json
from queue import Queue
import util

# Server Configuration
IP = '127.0.0.1'
PORT = 8087
BUFLEN = 1024

# Global Variables
clients = {}  # Stores connected clients {username: (socket, address)}
meetings = {} # Stores meetings {conference_id: [username1, username2, ...]}
lock = threading.Lock()

class ServerConference:
    def __init__(self, ):
        
        self.conference_id = None  # conference_id for distinguish difference conference
        self.conf_serve_ports = None
        self.data_serve_ports = {}
        self.data_types = ['screen', 'camera', 'audio']  # example data types in a video conference
        self.clients_info = None
        self.client_conns = None
        self.mode = 'Client-Server'  # or 'P2P' if you want to support peer-to-peer conference mode

    def handle_data(self, client_socket, data_type):
        """
        运行任务：接收来自客户端的共享流数据，并决定如何将其转发给其他客户端
        """
        try:
            while True:
                data = client_socket.recv(BUFLEN)  # 接收数据
                if not data:
                    break  # 连接关闭

                # 将数据转发给会议中的其他客户端
                with lock:
                    for username in meetings[self.conference_id]:
                        if username != client_socket.getpeername()[0]:  # 排除发送者
                            target_socket, _ = clients[username]
                            try:
                                target_socket.send(data)
                            except:
                                print(f"[Error] 发送数据给 {username} 失败")
                print(f"[Info] {data_type} 数据已转发给会议 {self.conference_id} 中的其他参与者")
        except Exception as e:
            print(f"[Error] 处理 {data_type} 数据时出错: {e}")
        finally:
            client_socket.close()

    def handle_client(self, client_socket, address):
        """
        运行任务：处理来自客户端的会议请求或消息
        """
        username = None
        try:
            while True:
                data = client_socket.recv(BUFLEN).decode()  # 接收客户端请求
                if not data:
                    break  # 如果没有数据则跳出循环

                request = json.loads(data)  # 解析请求
                print(request)
                action = request.get("action")

                if action == "login":
                    username = request.get("username")
                    with lock:
                        if username not in clients:
                            clients[username] = (client_socket, address)
                            response = {"status": "success", "message": "Login successful."}
                            print(f"[Info] {username} 登陆成功")
                        else:
                            response = {"status": "error", "message": "Username already taken."}
                    client_socket.send(json.dumps(response).encode('utf-8'))

                elif action == "create_conference":
                    conference_id = request.get("conference_id")
                    self.conference_id = conference_id
                    with lock:
                        if conference_id not in meetings:
                            meetings[conference_id] = [username]
                            self.data_serve_ports[conference_id] = {}  # 初始化会议的端口
                            response = {"status": "success", "conference_id": conference_id}
                            print(f"[Info] {username} 创建会议 {conference_id}")
                        else:
                            response = {"status": "error", "message": "Conference ID already exists."}
                    client_socket.send(json.dumps(response).encode('utf-8'))

                elif action == "join_conference":
                    conference_id = request.get("conference_id")
                    with lock:
                        if conference_id in meetings and username not in meetings[conference_id]:
                            meetings[conference_id].append(username)
                            self.conference_id = conference_id
                            response = {"status": "success", "conference_id": conference_id}
                            print(f"[Info] {username} 加入会议 {conference_id}")
                        else:
                            response = {"status": "error", "message": "Conference not found or already joined."}
                    client_socket.send(json.dumps(response).encode('utf-8'))

                elif action == "quit_conference":
                    conference_id = request.get("conference_id")
                    with lock:
                        if conference_id in meetings and username in meetings[conference_id]:
                            meetings[conference_id].remove(username)
                            response = {"status": "success"}
                            print(f"[Info] {username} 退出会议 {conference_id}")
                        else:
                            response = {"status": "error", "message": "You are not in this conference."}
                    client_socket.send(json.dumps(response).encode('utf-8'))

                elif action == "cancel_conference":
                    conference_id = request.get("conference_id")
                    with lock:
                        if conference_id in meetings and username in meetings[conference_id]:
                            del meetings[conference_id]
                            response = {"status": "success"}
                            print(f"[Info] {username} 取消会议 {conference_id}")
                        else:
                            response = {"status": "error", "message": "You cannot cancel this conference."}
                    client_socket.send(json.dumps(response).encode('utf-8'))

        except Exception as e:
            print(f"[Error] Exception occurred with {username}: {e}")
        finally:
            if username:
                with lock:
                    clients.pop(username, None)
                print(f"[Info] {username} 断开连接")
            client_socket.close()


    def log(self, message):
        print(f"[INFO]:{message}")

    def cancel_conference(self):
        """
        处理取消会议请求：断开所有连接并取消会议
        """
        with lock:
            if self.conference_id in meetings:
                for username in meetings[self.conference_id]:
                    client_socket, _ = clients.get(username, (None, None))
                    if client_socket:
                        try:
                            client_socket.close()
                        except Exception as e:
                            print(f"[Error] 关闭连接时出错: {e}")
                del meetings[self.conference_id]
                print(f"[Info] 会议 {self.conference_id} 已取消")


    def start(self):
        """
        启动 ConferenceServer，监听客户端连接并处理会议相关任务
        """
        while True:
            client_socket, address = self.server_socket.accept()
            print(f"[Connection] New connection from {address}")

            # 为每个客户端创建一个新的线程
            threading.Thread(target=self.handle_client, args=(client_socket, address)).start()



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
                action = request.get("acti")

                if action == "login":
                    username = request.get("username")
                    with lock:
                        if username not in clients:
                            clients[username] = (client_socket, address)
                            response = {"status": "success", "message": "Login successful."}
                            print(f"[Info] {username} logged in from {address}")
                        else:
                            response = {"status": "error", "message": "Username already taken."}
                    client_socket.send(json.dumps(response).encode('utf-8'))

                elif action == "create_conference":
                    conference_id = util.generate_code()
                    meetings[conference_id] = [username]
                    response = {"status": "success", "conference_id": conference_id}
                    print(f"[Info] Conference {conference_id} created by {username}")
                    client_socket.send(json.dumps(response).encode('utf-8'))

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
                    client_socket.send(json.dumps(response).encode('utf-8'))

                elif action == "quit_conference":
                    conference_id = request.get("conference_id")
                    with lock:
                        if conference_id in meetings and username in meetings[conference_id]:
                            meetings[conference_id].remove(username)
                            response = {"status": "success"}
                            print(f"[Info] {username} left conference {conference_id}")
                        else:
                            response = {"status": "error", "message": "You are not in this conference."}
                    client_socket.send(json.dumps(response).encode('utf-8'))

                elif action == "cancel_conference":
                    conference_id = request.get("conference_id")
                    with lock:
                        if conference_id in meetings and username in meetings[conference_id]:
                            del meetings[conference_id]
                            response = {"status": "success"}
                            print(f"[Info] {username} canceled conference {conference_id}")
                        else:
                            response = {"status": "error", "message": "You cannot cancel this conference."}
                    client_socket.send(json.dumps(response).encode('utf-8'))

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
