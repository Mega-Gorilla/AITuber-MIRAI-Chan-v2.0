import re
import pytchat
from pytchat import LiveChatAsync
import time
from rich_desgin import error
import asyncio

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

def get_new_comments(chat):
    """
    新しいコメントを取得し、リストとして返す。
    """
    new_comments = []
    while chat.is_alive():
        for c in chat.get().sync_items():
            new_comments.append({'name': c.author.name, 'comment': c.message})
        break  # ループを一度だけ実行
    return new_comments

async def get_new_commentsAsync(chat, last_comment_id=None):
    """
    新しいコメントを取得し、リストとして返す。
    """
    new_comments = []
    while chat.is_alive():
        for c in chat.get().sync_items():
            if last_comment_id is None or c.id > last_comment_id:
                new_comments.append({'name': c.author.name, 'comment': c.message})
                last_comment_id = c.id
        break  # ループを一度だけ実行
    return new_comments, last_comment_id

def create_pychat(URL):# ビデオIDを抽出
    video_id = extract_video_id(URL)
    if not video_id:
        error("pychat error","Invalid YouTube URL",{"Youtube URL":URL})
        return None
    chat = pytchat.create(video_id=video_id)
    return chat

async def youtube_liveChat_fetch(URL=None,chat=None):
    if chat is None:
        chat = create_pychat(url)
    try:
        # 新しいコメントを取得
        new_comments = get_new_comments(chat)
        
        return new_comments
        # ロギング（ここでは単にプリントしていますが、ファイルに保存するなどが可能です）

    except Exception as e:
        error("Live Chat Fetch Error:", f"{e}", {"URL":URL,"Chat":chat})
        print("Stopped.")

async def loop_test(chat,interval_s=5):
    while True:
        new_comments = await youtube_liveChat_fetch(chat=chat)
        for comment in new_comments:
            print(f"{comment['name']}: {comment['comment']}")
        await asyncio.sleep(interval_s)


if __name__ == "__main__":
    url='https://www.youtube.com/watch?v=_p2zEtZR5OQ'
    chat=create_pychat(url)
    asyncio.run(loop_test(chat))