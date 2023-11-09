from module.server_requests import *
import re
import pytchat
import asyncio
import requests
try:
    from module.rich_desgin import error
except ImportError:
    from rich_desgin import error

def extract_video_id(url):
    """
    YouTubeのURLからビデオIDを抽出する。
    """
    
    if "youtube.com" in url:
        # 正規表現を用いてvパラメータを検出する。
        match = re.search(r"v=([a-zA-Z0-9_-]{11})", url)
        return match.group(1) if match else None
    elif "youtu.be" in url:
        # 短縮URLからIDを抽出する。
        match = re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", url)
        return match.group(1) if match else None

def get_channel_id(URL,API_key):
    video_id = extract_video_id(URL)
    # YouTube Data APIのURLを構築
    url = f'https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={API_key}&part=snippet'

    # APIリクエストを送信してレスポンスを取得
    response = requests.get(url)
    data = response.json()

    # チャンネルIDを取得
    channel_id = data['items'][0]['snippet']['channelId']
    return channel_id

def get_new_comments(chat):
    """
    YouTubeのライブチャットから新しいコメントを取得します。

    この関数は、指定された `chat` オブジェクトが生きている（アクティブなチャットセッションが存在する）間、
    新しいチャットメッセージを継続的にポーリングします。各メッセージについて、
    その情報を含む辞書を作成し、リストに追加します。

    メッセージがスーパーチャット（投げ銭）の場合、対応するブール値（`superchat_bool`）、
    金額（`superchat_value`）、通貨（`superchat_currency`）を記録します。

    注意: この関数は現在、ループを1回だけ実行し、その時点で利用可能なコメントをすべて取得します。

    パラメータ:
        chat (pytchat.Chat): pytchatを通じて生成されたYouTubeライブチャットオブジェクト。

    戻り値:
        list of dict: 各コメントの情報を含む辞書のリスト。
            - 'name' (str): コメントの著者の名前。
            - 'comment' (str): コメントのテキスト。
            - 'timestamp' (int): コメントが投稿されたタイムスタンプ。
            - 'superchat_bool' (bool): コメントがスーパーチャットであるかどうか。
            - 'superchat_value' (float): スーパーチャットの金額。
            - 'superchat_currency' (str): スーパーチャットの通貨。

    参考:
        pytchatのデフォルトプロセッサに関する詳細は以下のURLを参照してください。
        https://github.com/taizan-hokuto/pytchat/wiki/DefaultProcessor_
    """
    new_comments = []
    while chat.is_alive():
        for c in chat.get().sync_items():
            if c.amountValue>0:
                superchat_bool=True
            else:
                superchat_bool=False
            new_comments.append({'name': c.author.name, 'comment': c.message,'timestamp':c.timestamp,'superchat_bool':superchat_bool,'superchat_value':c.amountValue,'superchat_currency':c.currency})
        break  # ループを一度だけ実行
    return new_comments

def create_pychat(URL):# ビデオIDを抽出
    video_id = extract_video_id(URL)
    if not video_id:
        error("pychat error","Invalid YouTube URL",{"Youtube URL":URL})
        return None
    chat = pytchat.create(video_id=video_id)
    return chat

async def youtube_liveChat_fetch(URL=None,chat=None):
    """
    YouTubeライブチャットからリアルタイムでコメントを取得します。

    指定されたURLからライブチャットを作成し、そのチャットオブジェクトを通じて
    新しいコメントのリストを取得します。コメントは辞書のリストとして返され、
    各辞書にはコメント投稿者の名前、コメント内容、タイムスタンプ、スーパーチャットに関する情報が含まれます。

    もし `chat` パラメータが None であれば、`URL` を使って新しいチャットオブジェクトを作成します。
    この関数は非同期で実行されるため、`await` を使用して呼び出す必要があります。

    戻り値の例:
    [
        {'name': '高山はるかしゅ', 'comment': '笹', 'timestamp': 1698983722670,
         'superchat_bool': False, 'superchat_value': 0.0, 'superchat_currency': ''},
        ...
    ]

    パラメータ:
        URL (str): YouTubeライブチャットのURL。chatがNoneの場合に使用されます。
        chat (Chat): pytchatを使用して生成されたチャットオブジェクト。
                     このパラメータが提供されている場合、URLは無視されます。

    戻り値:
        list of dict: チャットの各コメント情報を含む辞書のリスト。
            各辞書は以下のキーを持ちます:
            - 'name' (str): コメント投稿者の名前。
            - 'comment' (str): コメントの内容。
            - 'timestamp' (int): コメントが投稿された時のUNIXタイムスタンプ。
            - 'superchat_bool' (bool): コメントがスーパーチャットであるかどうか。
            - 'superchat_value' (float): スーパーチャットの金額。
            - 'superchat_currency' (str): スーパーチャットで使用された通貨。

    例外:
        この関数は、チャットの取得中に発生する可能性のある任意の例外をキャッチし、
        エラーログに記録した後、処理を停止します。
    """
    if chat is None:
        chat = create_pychat(url)
    try:
        # 新しいコメントを取得
        new_comments = get_new_comments(chat)
        
        return new_comments

    except Exception as e:
        error("Live Chat Fetch Error:", f"{e}", {"URL":URL,"Chat":chat})
        print("Stopped.")

async def youtube_viewer_count(URL,API_key):
    video_id = extract_video_id(URL)
    # YouTube Data APIのURL
    api_url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&part=liveStreamingDetails&key={API_key}"
    responce = await get_data_from_server(api_url)
    # レスポンスから視聴者数を抽出
    if 'liveStreamingDetails' in responce['items'][0]:
        viewer_count = responce['items'][0]['liveStreamingDetails'].get('concurrentViewers')
        return {'ok':True,'viewer_count':viewer_count}
    else:
        return{'ok':False,'message':'Live streaming details could not be found.'}

async def youtube_subscriber_count(channel_ID,API_key):
    api_url = f'https://www.googleapis.com/youtube/v3/channels?part=statistics&id={channel_ID}&key={API_key}'
    responce = await get_data_from_server(api_url)
    subscriber_count = responce['items'][0]['statistics']['subscriberCount']
    return {'ok':True,'subscriber_count':subscriber_count}

async def loop_test(chat,interval_s=5):
    while True:
        new_comments = await youtube_liveChat_fetch(chat=chat)
        print(new_comments)
        for comment in new_comments:
            if comment['superchat_bool']:
                print(f"SUPER CHAT!!! {comment['superchat_currency']} {comment['superchat_value']}/{comment['name']}: {comment['comment']}")
            else:
                print(f"{comment['name']}: {comment['comment']}")
        await asyncio.sleep(interval_s)


if __name__ == "__main__":
    url='https://www.youtube.com/watch?v=_p2zEtZR5OQ'
    chat=create_pychat(url)
    asyncio.run(loop_test(chat))