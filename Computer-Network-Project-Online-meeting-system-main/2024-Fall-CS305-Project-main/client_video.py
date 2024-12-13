import socket
import numpy as np
from PIL import Image
import io
from util import *

# 设置服务器地址和端口
SERVER_ADDRESS = ('127.0.0.1', 12345)
BUFFER_SIZE = 4096  # 每次发送的最大数据量



def send_image(socket, image):
    byte_arr =compress_image(image)

    # 发送图像数据
    socket.sendall(len(byte_arr).to_bytes(4, 'big'))  # 发送图像的大小（4字节）
    socket.sendall(byte_arr)  # 发送图像数据

def receive_image(socket):
    """
    接收服务器发送的图像数据，并解码为PIL图像
    :param socket: 客户端socket
    :return: PIL图像对象
    """
    # 接收图像的大小（前4字节）
    data_size = socket.recv(4)
    if not data_size:
        return None
    data_size = int.from_bytes(data_size, 'big')

    # 接收完整的图像数据
    image_data = b""
    while len(image_data) < data_size:
        image_data += socket.recv(BUFFER_SIZE)

    # 解码图像数据
    image = Image.open(io.BytesIO(image_data))
    return image

def main():
    # 连接到服务器
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(SERVER_ADDRESS)

    try:
        while True:
            # 从服务器接收并解码图像
            image = receive_image(client_socket)
            if image is None:
                print("No image received, exiting...")
                break

            # 将PIL图像转换为OpenCV格式（NumPy数组）
            image_cv = np.array(image)

            # 转换为BGR格式（OpenCV使用BGR而不是RGB）
            image_cv = cv2.cvtColor(image_cv, cv2.COLOR_RGB2BGR)

            # 显示图像
            cv2.imshow("Video Stream", image_cv)

            # 按 'q' 键退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        # 关闭socket和窗口
        client_socket.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()