from util import *
import asyncio
from datetime import datetime, timedelta
class UDPVideoProtocol:
    DATA_MAP={}
    CHUNK_SIZE=1400
    CASH_SIZE=30
    QUEUE_MAP = {}
    SEQUENCE_NUMBER=0
    def __init__(self):
        self.transport = None
    def connection_made(self, transport):
        """
        当 UDP 连接被创建时调用
        """
        self.transport = transport
        print("UDP 服务器已启动")
    
    def error_received(self, exc):
        """
        当底层 UDP 传输发生错误时调用
        :param exc: Exception 对象，表示发生的错误
        """
        if exc:
            print(f"接收到错误: {exc}")
        else:
            print("接收到未知的错误")

    def datagram_received(self,data,addr):
        """
        处理接收到的分片，并尝试重组完整数据
        :param data_map: 存储每个地址的分片数据
        :param data: 收到的数据
        :param addr: 发送方地址
        :return: 完整数据（如果已重组完成），否则返回 None
        """
        if addr not in self.QUEUE_MAP:
            self.QUEUE_MAP[addr] =asyncio.Queue(maxsize=self.CASH_SIZE)
            print(f"新客户端连接: {addr},数据缓存队列初始化完成")
       

        header, chunk = data.split(b"|", 1)  # 分离头部和数据
        header_parts=header.decode().split("/")
        datatype=header_parts[0]
        sequence_number,index, total = map(int, header_parts[1:])  # 解析头部
        
        if addr not in self.DATA_MAP:
        # 如果 `addr` 不在 `DATA_MAP` 中，初始化为一个空字典
            self.DATA_MAP[addr] = {}

        # if datatype not in self.DATA_MAP[addr]:
        #     # 如果 `datatype` 不在 `addr` 的字典中，初始化为一个空字典
        #     self.DATA_MAP[addr][datatype] = {}

        if sequence_number not in self.DATA_MAP[addr]:
            # 如果 `sequence_number` 不在 `datatype` 的字典中，初始化为一个空字典
            self.DATA_MAP[addr][sequence_number] = [None]*total

        self.DATA_MAP[addr][sequence_number][index] = chunk  # 存储当前分片        
        
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
        

    async def send_image(self, image,addr):
        """
        发送图片到服务端
        :param image: 要发送的 PIL 图片
        """
        from util import compress_image  # 确保使用的压缩函数正确
        image = image.convert("RGB")
        byte_arr = compress_image(image)
        # print(f'data size: {len(byte_arr)}')
        await self.send_large_data(byte_arr,addr,'image')
    
    async def send_audio(self, audio,addr):
        """
        发送音频到服务端
        :param audio: 要发送的音频数据
        """
        await self.send_large_data(audio,addr,'audio')

    async def send_large_data(self,data,addr,type):
        """
        将大数据分片发送
        :param transport: UDP transport
        :param data: 要发送的字节数据
        :param addr: 目标地址
        """

        total_chunks = (len(data) + self.CHUNK_SIZE - 1) // self.CHUNK_SIZE  # 计算总片数
        for i in range(total_chunks):
            # 提取当前片段
            chunk = data[i * self.CHUNK_SIZE:(i + 1) * self.CHUNK_SIZE]
            # 添加片段序号和总片数作为头部
            if(type=='image'):
                header = f"M/{self.SEQUENCE_NUMBER}/{i}/{total_chunks}".encode()  # 格式：片号/总片数
            elif(type=='audio'):
                header = f"A/{self.SEQUENCE_NUMBER}/{i}/{total_chunks}".encode()
            try:
                # 发送数据
                self.transport.sendto(header + b"|" + chunk, addr)
                # print(f"发送数据分片 {i + 1}/{total_chunks} 到 {addr}")
            except Exception as e:
                print(f"发送分片时出错: {e}")
            await asyncio.sleep(0.0001)
        self.SEQUENCE_NUMBER+=1    

    def connection_lost(self, exc):
        """
        当 UDP 连接丢失或关闭时调用
        :param exc: 异常对象（如果有），否则为 None
        """
        if exc:
            print(f"连接丢失，异常：{exc}")
        else:
            print("连接正常关闭")
    
    async def get_a_frame(self, addr):
        """
        从指定客户端地址的队列中获取一帧数据
        """
        if addr in self.QUEUE_MAP:
            try:
                byte=await self.QUEUE_MAP[addr].get()
                image=decompress_image(byte)
                return image
            except asyncio.QueueEmpty:
                print('队列空')
                return None
        else:
            raise KeyError(f"客户端地址 {addr} 不存在")
    
    async def get_an_audio_frame(self,addr):
        """
        从指定客户端地址的队列中获取一帧音频数据
        """
        if addr in self.QUEUE_MAP:
            try:
                byte=await self.QUEUE_MAP[addr].get()
                print(f'音频帧格式是：{type(byte)}')
                return byte
            except asyncio.QueueEmpty:
                print('队列空')
                return None
        else:
            raise KeyError(f"客户端地址 {addr} 不存在")
        
    

    