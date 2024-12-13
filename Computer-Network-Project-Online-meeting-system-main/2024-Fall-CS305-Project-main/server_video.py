import socket
import threading
from PIL import Image, ImageDraw
import io
import numpy as np
import cv2
from util import overlay_camera_images

# 服务端配置
SERVER_ADDRESS = ('127.0.0.1', 12345)
BUFFER_SIZE = 4096  # 每次接收的最大数据量
CLIENTS = []  # 保存所有连接的客户端


def handle_client(client_socket):
    """
    处理与客户端的连接
    :param client_socket: 客户端socket
    """
    global CLIENTS
    try:
        while True:
            # 接收图像数据的大小
            data_size = client_socket.recv(4)
            if not data_size:
                break
            data_size = int.from_bytes(data_size, 'big')

            # 接收图像数据
            image_data = b""
            while len(image_data) < data_size:
                image_data += client_socket.recv(BUFFER_SIZE)

            # 将图像数据转换为PIL图像
            image = Image.open(io.BytesIO(image_data))

            # 将图像添加到客户端列表中
            CLIENTS.append(image)

            # 合成图像
            result_image = overlay_camera_images(CLIENTS)

            # 将合成图像广播给所有客户端
            if result_image:
                for client in CLIENTS:
                    send_image(client_socket, result_image)

    finally:
        CLIENTS.remove(client_socket)
        client_socket.close()

def send_image(client_socket, image):
    """
    将图像数据发送给客户端
    :param client_socket: 客户端socket
    :param image: 要发送的PIL图像
    """
    byte_arr = io.BytesIO()
    image.save(byte_arr, format='JPEG')
    byte_arr = byte_arr.getvalue()

    # 发送图像的大小和数据
    client_socket.sendall(len(byte_arr).to_bytes(4, 'big'))
    client_socket.sendall(byte_arr)

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(SERVER_ADDRESS)
    server_socket.listen(5)
    print(f"Server listening on {SERVER_ADDRESS}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"New client connected: {client_address}")

            # 创建新线程来处理客户端
            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.start()
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()