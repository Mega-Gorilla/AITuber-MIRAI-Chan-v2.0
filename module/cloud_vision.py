from google.cloud import vision
from module.screenshot import *
import io,os,time

def cloud_vision_OCR(img):
    """Cloud Vision APIを使用して画像からテキストを検出する関数"""
    # クライアントライブラリのインスタンスを生成
    client = vision.ImageAnnotatorClient()

    # PIL Imageオブジェクトをバイト列に変換
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    content = img_byte_arr.getvalue()

    # Cloud Vision APIに渡すための画像オブジェクトを作成
    image = vision.Image(content=content)

    # 画像からテキストを検出するリクエストを実行
    response = client.text_detection(image=image)
    texts = response.text_annotations
    # レスポンスからテキストを表示
    print(texts[0].description)

    # 応答にエラーが含まれているかどうかを確認
    if response.error.message:
        raise Exception(f"{response.error.message}\nFor more info on error messages, check: https://cloud.google.com/apis/design/errors")
    
    return texts[0].description

if __name__ == "__main__":
    #ライセンス設定
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] ="D:\\GoogleDrive\\solo\\key\\ai-tuber-api-dc0b1b81cad7.json"
    processtime= time.time()
    # 使用例
    monitor_number = 1  # 1番目のモニター
    screenshot = take_screenshot(monitor_number)
    crop_area = (725, 1555, 3050, 2100)  
    cropped_screenshot = crop_image(screenshot, crop_area)
    cropped_screenshot = fill_non_white_pixels_black(cropped_screenshot)
    cloud_vision_OCR(cropped_screenshot)
    print(f"\nocr time:{time.time()-processtime}\n\n")
    