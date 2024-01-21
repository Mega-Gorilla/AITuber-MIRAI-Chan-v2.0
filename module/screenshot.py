import mss
import mss.tools
from PIL import Image
import numpy as np

def take_screenshot(monitor_number=1):
    """指定されたモニターのスクリーンショットを撮影する関数"""
    with mss.mss() as sct:
        monitors = sct.monitors
        try:
            # 指定されたモニター番号が存在するか確認
            monitor = monitors[monitor_number]
        except IndexError:
            # 存在しない場合はエラーメッセージを表示して関数を終了
            print(f"Error: Monitor number {monitor_number} is not available.")
            print(f"Available monitors are 1 to {len(monitors) - 1}.")
            return {'ok':False,'Error':f"Error: Monitor number {monitor_number} is not available.\nAvailable monitors are 1 to {len(monitors) - 1}."}
        screenshot = sct.grab(monitor)
        
        # スクリーンショットをPIL Imageオブジェクトに変換
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        return {'ok':True,"img":img}

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
    # PIL ImageをNumPy配列に変換
    data = np.array(image)
    
    # RGB各チャンネルが255以外のピクセルを黒色にする
    # 白以外（R,G,Bのいずれかが255以外）のマスクを作成し、それを用いてピクセルを黒に設定
    non_white_pixels_mask = (data[:, :, :3] != 255).any(axis=2)
    data[non_white_pixels_mask] = [0, 0, 0]
    
    # NumPy配列をPIL Imageに変換して返す
    return Image.fromarray(data, 'RGB')

if __name__ == "__main__":
    # 使用例
    monitor_number = 1  # 1番目のモニター
    screenshot = take_screenshot(monitor_number)
    if screenshot['ok']:
        screenshot = screenshot['img']
    else:
        raise ValueError(screenshot['Error'])
    crop_area = [725, 1555, 3050, 2100]
    cropped_screenshot = crop_image(screenshot, crop_area)
    cropped_screenshot = fill_non_white_pixels_black(cropped_screenshot)
    save_path = f"cropped_monitor_{monitor_number}.png"
    save_image(cropped_screenshot, save_path)