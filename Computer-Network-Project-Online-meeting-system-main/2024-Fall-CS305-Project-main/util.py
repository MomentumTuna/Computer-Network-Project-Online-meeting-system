'''
Simple util implementation for video conference
Including data capture, image compression and image overlap
Note that you can use your own implementation as well :)
'''
from io import BytesIO
import pyaudio
import cv2
import pyautogui
import numpy as np
from PIL import Image, ImageGrab
from config import *



# audio setting
FORMAT = pyaudio.paInt16
audio = pyaudio.PyAudio()
streamin = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=AUDIO_CHUNK)
streamout = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=AUDIO_CHUNK)

# print warning if no available camera
cap = cv2.VideoCapture(0)
if cap.isOpened():
    can_capture_camera = True
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)
else:
    can_capture_camera = False

my_screen_size = pyautogui.size()

def audio_device_info():
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        print(f"设备索引: {i}, 设备名称: {info['name']}, 最大输入通道数: {info['maxInputChannels']}")

def mix_audio(audio_list):
    """
    混合多个字节流音频数据
    :param audio_list: list of bytes, 每个音频帧的字节流
    :return: bytes, 混合后的音频数据（字节流）
    """
    if not audio_list:  # 如果列表为空，返回空字节
        return b''

    # 将字节流转换为 NumPy 数组
    audio_arrays = [np.frombuffer(audio, dtype=np.int16) for audio in audio_list]

    # 找到最大长度
    max_length = max(len(arr) for arr in audio_arrays)

    # 填充数组以使形状一致
    audio_arrays = [np.pad(arr, (0, max_length - len(arr)), mode='constant') for arr in audio_arrays]

    # 转换为高精度类型以避免溢出
    audio_arrays = [arr.astype(np.int32) for arr in audio_arrays]

    # 求和
    mixed_audio = np.sum(audio_arrays, axis=0)

    # 限制范围并转换回 int16
    mixed_audio = np.clip(mixed_audio, -32768, 32767).astype(np.int16)

    # 转换为字节流并返回
    return mixed_audio.tobytes()

def audio_out(frame):
    streamout.write(frame)

def resize_image_to_fit_screen(image, my_screen_size):
    screen_width, screen_height = my_screen_size

    original_width, original_height = image.size

    aspect_ratio = original_width / original_height

    if screen_width / screen_height > aspect_ratio:
        # resize according to height
        new_height = screen_height
        new_width = int(new_height * aspect_ratio)
    else:
        # resize according to width
        new_width = screen_width
        new_height = int(new_width / aspect_ratio)

    # resize the image
    resized_image = image.resize((new_width, new_height), Image.LANCZOS)

    return resized_image


def overlay_camera_images(screen_image, camera_images):
    """
    screen_image: PIL.Image
    camera_images: list[PIL.Image]
    """
    if screen_image is None and camera_images is None:
        print('[Warn]: cannot display when screen and camera are both None')
        return None
    if screen_image is not None:
        screen_image = resize_image_to_fit_screen(screen_image, my_screen_size)

    if camera_images is not None:
        # make sure same camera images
        if not all(img.size == camera_images[0].size for img in camera_images):
            raise ValueError("All camera images must have the same size")

        screen_width, screen_height = my_screen_size if screen_image is None else screen_image.size
        camera_width, camera_height = camera_images[0].size

        # calculate num_cameras_per_row
        num_cameras_per_row = screen_width // camera_width

        # adjust camera_imgs
        if len(camera_images) > num_cameras_per_row:
            adjusted_camera_width = screen_width // len(camera_images)
            adjusted_camera_height = (adjusted_camera_width * camera_height) // camera_width
            camera_images = [img.resize((adjusted_camera_width, adjusted_camera_height), Image.LANCZOS) for img in
                             camera_images]
            camera_width, camera_height = adjusted_camera_width, adjusted_camera_height
            num_cameras_per_row = len(camera_images)

        # if no screen_img, create a container
        if screen_image is None:
            display_image = Image.fromarray(np.zeros((camera_width, my_screen_size[1], 3), dtype=np.uint8))
        else:
            display_image = screen_image
        # cover screen_img using camera_images
        for i, camera_image in enumerate(camera_images):
            row = i // num_cameras_per_row
            col = i % num_cameras_per_row
            x = col * camera_width
            y = row * camera_height
            display_image.paste(camera_image, (x, y))

        return display_image
    else:
        return screen_image


def capture_screen():
    # capture screen with the resolution of display
    # img = pyautogui.screenshot()
    img = ImageGrab.grab()
    return img


def capture_camera():
    # capture frame of camera
    ret, frame = cap.read()
    if not ret:
        raise Exception('Fail to capture frame from camera')
    return Image.fromarray(frame)

def end_camera():
    cap.release()

def capture_voice():
    return streamin.read(AUDIO_CHUNK)


def compress_image(image, format='JPEG', quality=85):
    """
    compress image and output Bytes

    :param image: PIL.Image, input image
    :param format: str, output format ('JPEG', 'PNG', 'WEBP', ...)
    :param quality: int, compress quality (0-100), 85 default
    :return: bytes, compressed image data
    """
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format=format, quality=quality)
    img_byte_arr = img_byte_arr.getvalue()

    return img_byte_arr


def decompress_image(image_bytes):
    """
    decompress bytes to PIL.Image
    :param image_bytes: bytes, compressed data
    :return: PIL.Image
    """
    img_byte_arr = BytesIO(image_bytes)
    image = Image.open(img_byte_arr)

    return image


import random
import string

def generate_code(length=6):
    # 选择字符集：数字 + 大写字母 + 小写字母
    characters = string.digits + string.ascii_letters  # digits (0-9) + ascii_letters (a-zA-Z)
    
    # 随机选择 `length` 个字符组成码
    code = ''.join(random.choice(characters) for _ in range(length))
    
    return code