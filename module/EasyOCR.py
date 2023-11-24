import easyocr
import time
import pygetwindow as gw
import pyautogui
import numpy as np
from PIL import Image, ImageFilter

class config:
    reader = None

def fill_non_white_pixels_black(image):
    # 画像の各ピクセルをループ処理する
    for y in range(image.height):
        for x in range(image.width):
            # 白以外のピクセルを黒にする
            if image.getpixel((x, y)) != (255, 255, 255):
                image.putpixel((x, y), 0)
    return image

def take_screenshot_of_window(window_title, crop_area=None, white_pixels_black=False,save_image=False,save_path='screenshot.png'):
    try:
        # 特定のウィンドウを探す
        window = gw.getWindowsWithTitle(window_title)[0]
        window.minimize()
        window.restore()
        time.sleep(0.5)

        # ウィンドウのスクリーンショットを取る
        screenshot = pyautogui.screenshot(region=(window.left, window.top, window.width, window.height))
    except IndexError:
        print(f"No window found with title: {window_title}")
        return None
    
    # 必要に応じて画像を切り取る
    if crop_area:
        screenshot = screenshot.crop(crop_area)  # crop_areaは(x1, y1, x2, y2)の形式

    if white_pixels_black:
        screenshot = fill_non_white_pixels_black(screenshot)
    if save_image:
        screenshot.save(save_path)
        print(f"Screenshot saved to {save_path}. \nScreen Size: {window.width} / {window.height}")
    np_screenshot = np.array(screenshot)
    np_screenshot = np_screenshot[:, :, ::-1].copy()
    # 画像オブジェクトを返す
    return np_screenshot


def easyocr_render_reset(langages=['ja','en'],gpu=True):
    render = easyocr.Reader(langages, gpu=True, detector='dbnet18')
    return render

def Doki_Doki_Literature_Club_Get_str(reader,debug=False):
    screenshot = take_screenshot_of_window("Doki Doki Literature Club!", (800, 1550, 3000, 2000),True,False)
    if screenshot is not None:
        results = reader.readtext(screenshot)
        box_position = []
        text_data = {"name":"","text":""}
        for (bbox, text, prob) in results:
            if debug:
                print(f"{text} / XY:{bbox}",end='')
                if box_position != []:
                    print(f" /X-:{bbox[3][0]-box_position[3][0]} Y-:{bbox[3][1]-box_position[3][1]}")
                else:
                    print()
            
            if 5<=bbox[0][1]<=60:
                if text_data["name"] == "":
                    text_data["name"] = text
                else:
                    text_data["name"] += text
            else:
                if text_data["text"] == "":
                    text_data["text"] = text
                else:
                    text_data["text"] += text
            box_position = bbox
        return text_data
    else:
        return None

if __name__ == "__main__":
    config.reader = easyocr_render_reset()
    
    while True:
        process_time = time.time()
        str_data = Doki_Doki_Literature_Club_Get_str(config.reader)
        print(f"Time: {time.time()-process_time}")
        if str_data:
            print(str_data)
        else:
            print("画面がありません")
        if input("") =="Y":
            break