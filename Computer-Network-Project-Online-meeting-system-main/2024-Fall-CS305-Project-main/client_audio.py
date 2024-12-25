import asyncio
from util import *
import cv2
import numpy as np
from udp_video import*
from keyboard import*
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from config import CONFERENCE1_AUDIO_ADDRESS, CONFERENCE1_VIDEO_ADDRESS, CONFERENCE2_AUDIO_ADDRESS, CONFERENCE2_VIDEO_ADDRESS, CONFERENCE3_AUDIO_ADDRESS, CONFERENCE3_VIDEO_ADDRESS


class ClientAudioProtocol(UDPVideoProtocol):
    """
    客户端协议类，继承 UDPVideoProtocol
    """
    SERVER_ADDRESS=None
    def __init__(self,SERVER_ADDRESS):
        super().__init__()
        self.SERVER_ADDRESS=SERVER_ADDRESS

    async def get_an_audio_frame(self):
        return await super().get_an_audio_frame(self.SERVER_ADDRESS)


    async def audio_transport(self,state):
        """
        捕获屏幕并将其作为帧发送到服务端
        """
        isOpen=state['mic_enabled']
        isStreaming=state['is_image_transport_enabled']
        try:
            # 捕获屏幕或摄像头画面
            if(isStreaming):
                if(isOpen):
                    audio=capture_voice()
                else:
                    audio=capture_voice()
                    audio = np.zeros(1000, dtype=np.int16)
                    audio=audio.tobytes()  #无声音频
                await self.send_audio(audio, self.SERVER_ADDRESS)
            else:
                header = f"A/0/{1500}/{1500}".encode()
                self.transport.sendto(header + b"|" + b"", self.SERVER_ADDRESS)
                print("已经发送结束信号")

                # print("图像已发送")
        except Exception as e:
            print(f"发送音频时发生错误: {e}")
    
    

    async def play_audio(self,state):
        """
        从队列中获取帧并显示视频
        """
        # 从父类的异步队列中获取一帧数据
        if(state['is_image_transport_enabled']):
            try:
                    audio = await self.get_an_audio_frame()
            except Exception as e:
                    print(f"获取帧时发生错误: {e}")

            # 显示图片
            try:
                audio_out(audio)
            except Exception as e:
                print(f"播放音频时发生错误: {e}")
        
       
       
async def consule_input(state):
    """
    任务1：检测控制台输入并更新 state 字典
    """
    while True:
        print("请输入指令 ('a'：切换 mic_enabled，'b'：切换 is_image_transport_enabled，'q'：退出程序)：")
        user_input = await asyncio.get_event_loop().run_in_executor(None, input, ">>> ")

        if state['is_image_transport_enabled']==False:
            break
        if user_input == 'a':
            state['mic_enabled'] = not state['mic_enabled']
            print(f"麦克风状态: {state['mic_enabled']}")
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
    send_task=asyncio.create_task(protocol.audio_transport(state))
    play_task=asyncio.create_task(protocol.play_audio(state))
    await send_task
    await play_task
    print('任务进行中')


def check_exit(state):
    if(state['is_image_transport_enabled']==False):
        return True
    else:
        return False        

async def audio_streaming(address):
    """
    主函数，负责建立 UDP 客户端并启动任务
    """
    state = {
        'is_image_transport_enabled': True,
        'mic_enabled': True,
    }
    # 创建缓存队列
    # 获取当前事件循环
    loop = asyncio.get_running_loop()
    # 创建 UDP 客户端
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: ClientAudioProtocol(address,),
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
    try:
        asyncio.run(audio_streaming(CONFERENCE1_AUDIO_ADDRESS))
    except Exception as e:
        print(f"发生错误: {e}")
    print('后续逻辑')

    
