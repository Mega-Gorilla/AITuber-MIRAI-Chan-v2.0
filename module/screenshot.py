import mss
import mss.tools
from PIL import Image

def take_screenshot(monitor_number=1):
    """指定されたモニターのスクリーンショットを撮影する関数"""
    with mss.mss() as sct:
        monitors = sct.monitors
        monitor = monitors[monitor_number]
        screenshot = sct.grab(monitor)
        
        # スクリーンショットをPIL Imageオブジェクトに変換
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        return img

def crop_image(img, crop_area):
    """画像を特定の座標で切り抜く関数"""
    # 画像を切り抜き
    cropped_img = img.crop(crop_area)
    return cropped_img

def save_image(img, path):
    """画像を指定したパスに保存する関数"""
    img.save(path)
    print(f"画像が {path} として保存されました。")

def fill_non_white_pixels_black(image):
    """白ピクセル以外を塗りつぶします"""
    # 画像の各ピクセルをループ処理する
    for y in range(image.height):
        for x in range(image.width):
            # 白以外のピクセルを黒にする
            if image.getpixel((x, y)) != (255, 255, 255):
                image.putpixel((x, y), 0)
    return image

if __name__ == "__main__":
    # 使用例
    monitor_number = 1  # 1番目のモニター
    screenshot = take_screenshot(monitor_number)
    crop_area = (725, 1555, 3050, 2100)  
    cropped_screenshot = crop_image(screenshot, crop_area)
    cropped_screenshot = fill_non_white_pixels_black(cropped_screenshot)
    save_path = f"cropped_monitor_{monitor_number}.png"
    save_image(cropped_screenshot, save_path)