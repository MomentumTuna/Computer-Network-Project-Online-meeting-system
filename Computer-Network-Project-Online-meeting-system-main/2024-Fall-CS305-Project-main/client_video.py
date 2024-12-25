import asyncio
from util import *
import cv2
import numpy as np
from udp_video import*
from keyboard import*
from threading import Thread
from concurrent.futures import ThreadPoolExecutor

SERVER_ADDRESS = ('127.0.0.1', 11111)  # 服务端地址和端口
BUFFER_SIZE = 4096  # 每次接收的最大数据量
CACHE_SIZE = 30  # 缓存队列大小（存储 30 帧）


class ClientProtocol(UDPVideoProtocol):
    """
    客户端协议类，继承 UDPVideoProtocol
    """
    SERVER_ADDRESS=None
    def __init__(self,SERVER_ADDRESS,conference_id):
        super().__init__(conference_id)
        self.SERVER_ADDRESS=SERVER_ADDRESS

    async def get_a_frame(self):
        return await super().get_a_frame(SERVER_ADDRESS)


    async def image_transport(self,state):
        """
        捕获屏幕并将其作为帧发送到服务端
        """
        isOpen=state['camera_enabled']
        isStreaming=state['is_image_transport_enabled']
        try:
            # 捕获屏幕或摄像头画面
            if(isStreaming):
                if(isOpen):
                    image=capture_camera()
                else:
                    height, width= capture_camera().size  # 获取原图尺寸
                    image = np.zeros((height, width), dtype=np.uint8)  # 全黑图像
                    image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)) 

                    # 调用父类的 send_image 方法发送图像
                await self.send_image(image, self.SERVER_ADDRESS)
            else:
                header = f"{self.CONFERENCE_ID}/M/0/{1500}/{1500}".encode()
                self.transport.sendto(header + b"|" + b"", self.SERVER_ADDRESS)
                print("已经发送结束信号")
            
            # print("图像已发送")
        except Exception as e:
            print(f"发送图像时发生错误: {e}")
    
    

    async def play_video(self,state):
        """
        从队列中获取帧并显示视频
        """
        
                # 从父类的异步队列中获取一帧数据

                # 将二进制数据转换为图片
        if(state['is_image_transport_enabled']):
            try:
                    image = await self.get_a_frame()
                    # 将 PIL 图像转换为 OpenCV 格式
                    frame = np.array(image)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            except Exception as e:
                    print(f"获取帧时发生错误: {e}")

            # 显示图片
            try:
                cv2.imshow("Video Stream", frame)
                cv2.waitKey(2)
            except Exception as e:
                print(f"显示视频时发生错误: {e}")
        else:
            cv2.destroyAllWindows()
            print('关闭视频窗口')
            return
       
       
async def consule_input(state):
    """
    任务1：检测控制台输入并更新 state 字典
    """
    while True:
        print("请输入指令 ('a'：切换 camera_enabled，'b'：切换 is_image_transport_enabled，'q'：退出程序)：")
        user_input = await asyncio.get_event_loop().run_in_executor(None, input, ">>> ")

        if state['is_image_transport_enabled']==False:
            break
        if user_input == 'a':
            state['camera_enabled'] = not state['camera_enabled']
            print(f"摄像头状态: {state['camera_enabled']}")
        elif user_input == 'b':
            state['is_image_transport_enabled'] = not state['is_image_transport_enabled']
            print(f"传输状态切换为: {state['is_image_transport_enabled']}")
        elif user_input == 'q':
            print("退出程序...")
            state['exit'] = True
        else:
            print("无效指令，请重新输入。")


async def client_task(state,protocol):
    # 启动接收图片的任务
    send_task=asyncio.create_task(protocol.image_transport(state))
    play_task=asyncio.create_task(protocol.play_video(state))
    await send_task
    await play_task
    print('任务进行中')


def check_exit(state):
    if(state['is_image_transport_enabled']==False):
        return True
    else:
        return False        

async def video_streaming(address,conference_id):
    """
    主函数，负责建立 UDP 客户端并启动任务
    """
    state = {
        'is_image_transport_enabled': True,
        'camera_enabled': True,
        'mic_enabled':True
    }
    # 创建缓存队列
    # 获取当前事件循环
    loop = asyncio.get_running_loop()
    # 创建 UDP 客户端
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: ClientProtocol(address,conference_id),
        remote_addr=address
    )
    
    consule_task=asyncio.create_task(consule_input(state))
    try:
        while True:
            # await consule_input(state)
            await client_task(state,protocol)
            exit=check_exit(state)
            if(exit):
                await client_task(state,protocol)
                await consule_task(state)
                break
    except asyncio.CancelledError:
        pass
    finally: # 取消任务
        
        print('任务已完成')
        await asyncio.sleep(0.01)
        transport.close()
        # try:
        #     cv2.destroyWindow('Video Stream')
        # except Exception as e:
        #     print(f"关闭视频窗口时发生错误: {e}")
        print('已释放缓存')
        
        loop.stop()




if __name__ == "__main__":
    # 初始化共享状态
    # 启动异步主函数
    # executor = ThreadPoolExecutor(max_workers=2)
    asyncio.run(video_streaming(SERVER_ADDRESS,1))
    
    # executor.shutdown(wait=True)
    # print("线程池已关闭")
    print('后续逻辑')

    
