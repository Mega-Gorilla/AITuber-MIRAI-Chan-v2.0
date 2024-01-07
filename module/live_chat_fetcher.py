import re
import os
import asyncio
import requests

try:
    from module.rich_desgin import error
    from module.server_requests import *
except ImportError:
    from rich_desgin import error
    from server_requests import *

class config:
    pychat_model = None

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
    response = requests.get(url).json()

    # チャンネルIDを取得
    print(response)
    if 'error' in response:
        print(f"YouTube Data API Error\n{response['error']['message']}")
        return False
    else:
        channel_id = response['items'][0]['snippet']['channelId']
        return channel_id
    
    """
    {
    'error': {
        'code': 400,
        'message': 'API key not valid. Please pass a valid API key.',
        'errors': [{'message': 'API key not valid. Please pass a valid API key.', 'domain': 'global', 'reason': 'badRequest'}],
        'status': 'INVALID_ARGUMENT',
        'details': [{'@type': 'type.googleapis.com/google.rpc.ErrorInfo', 'reason': 'API_KEY_INVALID', 'domain': 'googleapis.com', 'metadata': {'service': 'youtube.googleapis.com'}}]
    }
}
    """

def get_new_comments(video_id,api_key):
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

    """
    comments_list = []
    # YouTube APIのURL
    live_chat_url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&part=liveStreamingDetails&key={api_key}"
    # ライブチャットIDを取得する
    response = requests.get(live_chat_url)
    if response.status_code == 200:
        live_chat_data = response.json()
        live_chat_id = live_chat_data.get('items', [])[0]['liveStreamingDetails'].get('activeLiveChatId')
        if live_chat_id:
            # ライブチャットのコメントを取得する
            live_chat_comments_url = f"https://www.googleapis.com/youtube/v3/liveChat/messages?liveChatId={live_chat_id}&part=id,snippet,authorDetails&key={api_key}"
            comments_response = requests.get(live_chat_comments_url)
            if comments_response.status_code == 200:
                comments_data = comments_response.json()
                for item in comments_data.get('items', []):
                    # コメントの情報を辞書として抽出
                    comment_info = {
                        'name': item['authorDetails']['displayName'],
                        'comment': item['snippet']['displayMessage'],
                        'timestamp': item['snippet']['publishedAt'],
                        'superchat_bool': 'superChatDetails' in item['snippet'],
                        'superchat_value': float(item['snippet'].get('superChatDetails', {}).get('amountMicros', 0)) / 1e6 if 'superChatDetails' in item['snippet'] else 0,
                        'superchat_currency': item['snippet'].get('superChatDetails', {}).get('currency', '')
                    }
                    comments_list.append(comment_info)
            else:
                {"ok":False,"message":f"Failed to get live chat messages: {comments_response.status_code}"}
        else:
            {"ok":False,"message":"No active live chat id found."}
    else:
        return{"ok":False,"message":f"Failed to get live chat ID: {response.status_code}"}
    return comments_list

async def youtube_viewer_count(URL,API_key):
    video_id = extract_video_id(URL)
    # YouTube Data APIのURL
    api_url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&part=liveStreamingDetails&key={API_key}"
    responce = await get_data_from_server(api_url)
    # レスポンスから視聴者数を抽出
    if 'liveStreamingDetails' in responce['items'][0]:
        viewer_count = responce['items'][0]['liveStreamingDetails'].get('concurrentViewers')
        return {'ok':True,'viewer_count':int(viewer_count)}
    else:
        return{'ok':False,'message':'Live streaming details could not be found.'}

async def youtube_subscriber_count(channel_ID,API_key):
    api_url = f'https://www.googleapis.com/youtube/v3/channels?part=statistics&id={channel_ID}&key={API_key}'
    responce = await get_data_from_server(api_url)
    subscriber_count = responce['items'][0]['statistics']['subscriberCount']
    return {'ok':True,'subscriber_count':int(subscriber_count)}

if __name__ == "__main__":
    url='https://www.youtube.com/watch?v=tfyTjeEgmDA'
    while True:
        
        new_comments = get_new_comments(extract_video_id(url),os.getenv("GOOGLE_API_KEY"))
        print(new_comments)
        for comment in new_comments:
            if comment['superchat_bool']:
                print(f"SUPER CHAT!!! {comment['superchat_currency']} {comment['superchat_value']}/{comment['name']}: {comment['comment']}")
            else:
                print(f"{comment['name']}: {comment['comment']}")
        asyncio.sleep(5)