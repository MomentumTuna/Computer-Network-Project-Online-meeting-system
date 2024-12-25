import asyncio
from util import *
from udp_video import UDPVideoProtocol
import numpy as np
import cv2
from datetime import datetime, timedelta

SERVER_ADDRESS = ('127.0.0.1', 11111)  # 服务端地址和端口


class ServerProtocol(UDPVideoProtocol):
    clients = set()  # 记录所有连接的客户端地址
    def __init__(self):
        super().__init__()
        self.clients = set()  # 记录所有连接的客户端地址
    
    def datagram_received(self,data,addr):
        """
        处理接收到的分片，并尝试重组完整数据
        :param data_map: 存储每个地址的分片数据
        :param data: 收到的数据
        :param addr: 发送方地址
        :return: 完整数据（如果已重组完成），否则返回 None
        """

        if addr not in self.clients:
            self.clients.add(addr)  # 记录新的客户端地址
            print(f"新客户端连接: {addr}")

        if addr not in self.QUEUE_MAP:
            self.QUEUE_MAP[addr] = asyncio.Queue(maxsize=self.CASH_SIZE)
            print(f"新客户端连接: {addr}")
        self.LAST_ACTIVATE_TIME[addr]=datetime.now()

        header, chunk = data.split(b"|", 1)  # 分离头部和数据
        index, total = map(int, header.decode().split("/"))  # 解析头部

        if index==1500 and total==1500:
            del self.QUEUE_MAP[addr]
            # del self.DATA_MAP[addr]
            self.clients.remove(addr)
            print(f"客户端断开连接: {addr}")
            return

        if addr not in self.DATA_MAP:
            self.DATA_MAP[addr] = [None] * total  # 初始化存储分片的列表
        self.DATA_MAP[addr][index] = chunk  # 存储当前分片


        # 如果所有分片都已接收，返回完整数据
        if all(self.DATA_MAP[addr]):
            complete_data = b"".join(self.DATA_MAP[addr])
            del self.DATA_MAP[addr]  # 清理已完成的记录
            try:
                # 将完整帧放入该客户端的队列
                self.QUEUE_MAP[addr].put_nowait(complete_data)

                # print(f"完整帧已存入队列: {addr}")
            except asyncio.QueueFull:
                self.QUEUE_MAP[addr].get_nowait()  # 丢弃最旧的帧
                self.QUEUE_MAP[addr].put_nowait(complete_data)
                # print(f"队列已满，丢弃数据: {addr}")

    async def broadcast_frames(self):
        """
        从队列中取出完整帧，并广播给所有客户端
        """
        try:
            # 并发从所有客户端获取帧
            image_list = await asyncio.gather(
                *(self.get_a_frame(client) for client in self.clients),
                return_exceptions=True  # 捕获可能的异常
            )
        except Exception as e:
            print(f"获取帧时出错: {e}")

        try:
            background = capture_screen()
            if len(image_list):
                all_image = overlay_camera_images(background, image_list)
            else:
                print('image_list is empty')
                all_image = background
        except Exception as e:
            print(f"合成图像时出错: {e}")
        
        try:
            # 将合成的图像广播给所有客户端
            await asyncio.gather(
                *(self.send_image(all_image, client) for client in self.clients),
                return_exceptions=True  # 捕获可能的异常
            )
            print('广播图像成功')
        except Exception as e:
            print(f"广播数据时出错: {e}")
        

    async def test():
        await asyncio.sleep(0.1)

        
    async def get_frames(self):
        try:
            image_list = []
            for client in self.clients:
                try:
                    frame = await self.get_a_frame(client)  # 顺序获取每个客户端的帧
                    image_list.append(frame)
                    print(f"从客户端 {client} 获取了一帧数据")
                except Exception as e:
                    print(f"获取客户端 {client} 的帧时出错: {e}")

            print(f"获取了 {len(image_list)} 帧")
        except Exception as e:
            print(f"获取帧时出错: {e}")

        # 捕获屏幕背景
        background = capture_screen()

        try:
            if len(image_list):
                all_image = overlay_camera_images(background, image_list)  # 合成图像
                print("合成了图像")
            else:
                all_image = background
        except Exception as e:
            print(f"合成图像时出错: {e}")

        # 顺序广播图像给客户端
        try:
            for client in self.clients:
                try:
                    await self.send_image(all_image, client)  # 逐一发送图像
                    print(f"发送了图像到客户端 {client}")
                except Exception as e:
                    print(f"向客户端 {client} 发送图像时出错: {e}")
        except Exception as e:
            print(f"发送图像时出错: {e}")

    


async def main(address):
    """
    主函数，启动服务端协议并处理数据
    """
    # 获取当前事件循环
    loop = asyncio.get_running_loop()

    # 创建 UDP 服务端
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: ServerProtocol(),
        local_addr=address
    )

    try:
        while True:
            # 启动广播任务
            broadcast_task = asyncio.create_task(protocol.broadcast_frames())
            await broadcast_task
    finally:
        transport.close()


if __name__ == "__main__":
    asyncio.run(main(SERVER_ADDRESS))
