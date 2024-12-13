import cv2
import numpy as np
from PIL import Image, ImageGrab
import pyautogui
from io import BytesIO
from util import *
from config import *



my_screen_size = pyautogui.size()

# 打开摄像头
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Cannot open camera")
    exit()



def main():
    try:
        while True:
            # 捕捉屏幕
            screen_img = capture_screen()

            # 捕捉摄像头画面
            camera_img = capture_camera()

            # 将摄像头图像和屏幕图像叠加
            result_image = overlay_camera_images(screen_img, [camera_img])

            # 显示叠加后的图像
            result_image.show()

            # 按Q键退出循环
            key = cv2.waitKey(1)
            if key == ord('q'):
                break
    finally:
        cap.release()

if __name__ == "__main__":
    main()
