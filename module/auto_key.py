import pygetwindow as gw
import keyboard
import traceback

def send_key_to_app(window_title, key):
    try:
        # 特定のウィンドウを取得
        windows = gw.getWindowsWithTitle(window_title)
        if not windows:
            # ウィンドウが見つからなかった場合の処理
            print(f"No window found with title: {window_title}")
            raise ValueError(f"No window found with title: {window_title}")
        
        # ウィンドウをアクティブ化（フォーカスを当てる）
        window = windows[0]
        if window.isMinimized:  # ウィンドウが最小化されている場合は復元
            window.restore()
        window.activate()
        
        # キー入力を送信
        keyboard.press_and_release(key)
        
    except Exception as e:
        # 予期せぬエラーが発生した場合の処理
        print(f"An error occurred: {e}")
        traceback.print_exc()
        # 必要に応じて、ここでエラーを再発生させるか、特定の処理を実行

if __name__ == "__main__":
    # 使用例
    send_key_to_app("Doki Doki Literature Club!", "space")
