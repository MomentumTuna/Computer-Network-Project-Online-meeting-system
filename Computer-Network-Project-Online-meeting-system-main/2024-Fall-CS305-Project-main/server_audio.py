import asyncio
from util import *
from udp_video import UDPVideoProtocol
import numpy as np
from multiprocessing import Process
from config import CONFERENCE1_AUDIO_ADDRESS, CONFERENCE1_VIDEO_ADDRESS, CONFERENCE2_AUDIO_ADDRESS, CONFERENCE2_VIDEO_ADDRESS, CONFERENCE3_AUDIO_ADDRESS, CONFERENCE3_VIDEO_ADDRESS

class ServerAudioProtocol(UDPVideoProtocol):
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
            # self.QUEUE_MAP[addr] = asyncio.Queue(maxsize=self.CASH_SIZE)
            self.QUEUE_MAP[addr] = asyncio.Queue(maxsize=self.CASH_SIZE)
            print(f"新客户端连接: {addr},数据缓存队列初始化完成")


        header, chunk = data.split(b"|", 1)  # 分离头部和数据
        header_parts=header.decode().split("/")
        datatype=header_parts[0]
        sequence_number,index, total = map(int, header_parts[1:])  # 解析头部

        if index==1500 and total==1500:
            del self.QUEUE_MAP[addr]
            # del self.DATA_MAP[addr]
            self.clients.remove(addr)
            print(f"客户端断开连接: {addr}")
            return

        if addr not in self.DATA_MAP:
        # 如果 `addr` 不在 `DATA_MAP` 中，初始化为一个空字典
            self.DATA_MAP[addr] = {}

        if sequence_number not in self.DATA_MAP[addr]:
            # 如果 `sequence_number` 不在 `datatype` 的字典中，初始化为一个空字典
            self.DATA_MAP[addr][sequence_number] = [None]*total

        self.DATA_MAP[addr][sequence_number][index] = chunk  # 存储当前分片
        print(f'存储当前音频分片{addr} {sequence_number} {index}')

        try:
        # 如果所有分片都已接收，返回完整数据
            for key1 in list(self.DATA_MAP[addr]):
                if all(self.DATA_MAP[addr][key1]):
                    complete_data = b"".join(self.DATA_MAP[addr][key1])
                    del self.DATA_MAP[addr][key1]  # 清理已完成的记录
                    try:
                        # 将完整帧放入该客户端的队列
                        self.QUEUE_MAP[addr].put_nowait(complete_data)
                        print(f"完整帧已存入队列:{key1}{addr}")
                    except asyncio.QueueFull:
                        self.QUEUE_MAP[addr].get_nowait()  # 丢弃最旧的帧
                        self.QUEUE_MAP[addr].put_nowait(complete_data)
                        # print(f"队列已满，丢弃数据: {addr}")
        except Exception as e:
            print(f"处理数据时发生错误: {e}")


    async def broadcast_frames(self):
        """
        从队列中取出完整帧，并广播给所有客户端
        """
        try:
            audio_list = []
            for client in self.clients:
                try:
                    frame = await self.get_an_audio_frame(client)  # 顺序获取每个客户端的帧
                    audio_list.append(frame)
                    print(f"从客户端 {client} 获取了一帧数据")
                except Exception as e:
                    print(f"获取客户端 {client} 的帧时出错: {e}")

            print(f"获取了 {len(audio_list)} 帧")
        except Exception as e:
            print(f"获取帧时出错: {e}")

        try:
            if len(audio_list):
                mixed_audio= mix_audio(audio_list)
            else:
                print('image_list is empty')
                mixed_audio = np.zeros(8000, dtype=np.int16) 
        except Exception as e:
            print(f"合成音频时出错: {e}")
        
        try:
            for client in self.clients:
                try:
                    await self.send_audio(mixed_audio, client)  # 逐一发送音频
                    print(f"发送了音频到客户端 {client}")
                except Exception as e:
                    print(f"向客户端 {client} 发送音频时出错: {e}")
        except Exception as e:
            print(f"发送音频时出错: {e}")
        await asyncio.sleep(0.001)


async def main(address):
    """
    主函数，启动服务端协议并处理数据
    """
    # 获取当前事件循环
    loop = asyncio.get_running_loop()

    # 创建 UDP 服务端
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: ServerAudioProtocol(),
        local_addr=address
    )

    try:
        while True:
            # 启动广播任务
            broadcast_task = asyncio.create_task(protocol.broadcast_frames())
            await broadcast_task
    finally:
        transport.close()

def run_conference_1():
    asyncio.run(main(CONFERENCE1_AUDIO_ADDRESS))

def run_conference_2():
    asyncio.run(main(CONFERENCE2_AUDIO_ADDRESS))

def run_conference_3():
    asyncio.run(main(CONFERENCE3_AUDIO_ADDRESS))

if __name__ == "__main__":
    p1 = Process(target=run_conference_1)
    # p2 = Process(target=run_conference_2)
    # p3 = Process(target=run_conference_3)

    p1.start()
    # p2.start()
    # p3.start()