
from module.live_chat_fetcher import create_pychat,youtube_liveChat_fetch,youtube_viewer_count
from module.find_similar import AnswerFinder
from fastapi import FastAPI,BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Any
import asyncio
import os

app = FastAPI(title='AI Tuber API',version='β1.1')

#将来的にDBに移行
Youtube_comments = []

class mic_setting:
    mic_recording_bool = False

class record_data:
    recorded_list = []

class AI_Tuber_setting:
    AI_talk_bool:bool = False
    live_comment_fetch:bool = False
    live_comment_list = []
    youtube_URL:str = ""
    interval_s:int = 3
    youtube_api_key = os.getenv("GOOGLE_API_KEY")

class AnswerFinder_settings:
    csv_directory = 'memory/example_tone'
    persist_directory = 'memory/ChromaDB'
    finder = None
    start = False

@app.post("/mic_recording_bool/post/", tags=["Mic Settings"])
def mic_post_item(mic_recodiong: bool = False):
    """
    マイクの音声認識 ON/OFF:
    - True : ON
    - False : OFF
    """
    mic_setting.mic_recording_bool = mic_recodiong
    return mic_recodiong

@app.get("/mic_recording_bool/get/", tags=["Mic Settings"])
def mic_get_item():
    """
    マイクの音声認識 状態確認
    """
    return mic_setting.mic_recording_bool

@app.post("/AI_talk_bool/post/", tags=["AI Tuber"])
def AI_talk_post_item(AI_talk: bool = False):
    """
    AI Tuber 発声プロセス開始
    - True : 発声プロセス開始
    """
    AI_Tuber_setting.AI_talk_bool = AI_talk
    return AI_talk

@app.get("/AI_talk_bool/get/", tags=["AI Tuber"])
def AI_talk_get_item():
    """
    AI Tuber 発声プロセス状態確認
    """
    return AI_Tuber_setting.AI_talk_bool

@app.get("/similar_dialogue/get/", tags=["AI Tuber"])
def similar_dialogue_get(str_dialogue:str,top_n:int = 3):
    """
    類似会話を検索し、結果を返します
    
    パラメータ:
    str_dialogue: 検索する文字列

    戻り値:
    - レスポンス例 {'text':こんにちわ,'score'"0.22}
    """
    if AnswerFinder_settings.start:
        result = AnswerFinder_settings.finder.find_similar_vector_store(str_dialogue,top_n)
        result.append({'ok':True})
    else:
        result = [{'ok':False,'message':'類似会話検索エンジンが初期化されていません'}]
    return result

@app.post("/similar_dialogue/start/", tags=["AI Tuber"])
def similar_dialogue_start(background_tasks: BackgroundTasks):
    """
    類似会話検索エンジンを初期化します。
    検索方式はsimilarity searchです。

    注意:
    - 会話例データ: {AnswerFinder_settings.csv_directory}に検索対象のデータが入っている必要があります。
    - Chroma DB: 作成したデータベースは、{AnswerFinder_settings.persist_directory}に保存されます。
    """
    background_tasks.add_task(create_or_load_chroma_db_background)
    return {'ok':True,'message':'similar_dialogue Start.'}

@app.post("/mic_recorded_list/post/", tags=["Mic Settings"])
def mic_recorded_dict_post(recorded_list: List[Any]):
    """
    マイク音声認識関数に文字列を追加
    - List[Any]: ["こんにちわ"]
    """
    record_data.recorded_list.append(recorded_list)
    return record_data.recorded_list

@app.get("/mic_recorded_list/get/", tags=["Mic Settings"])
def mic_recorded_dict_get(reset: bool = False):
    """
    マイク音声認識文字列を取得
    - reset にて、配列を初期化する
    """
    responce_data = record_data.recorded_list
    if reset:
        record_data.recorded_list = []
    return responce_data

@app.post("/youtube_api/set_stream_url/", tags=["Youtube API"])
def set_stream_url(url:str):
    """
    Youtubeコメント取得先URLを設定

    パラメータ:
    - url YoutubeURLを設定する

    戻り値:
    - {'ok':True,"message": url}
    """
    AI_Tuber_setting.youtube_URL = url
    return {'ok':True,"message": url}

@app.get("/youtube_api/get_stream_url/", tags=["Youtube API"])
def get_stream_url():
    """
    Youtubeコメント取得先URLを取得
    """
    return AI_Tuber_setting.youtube_URL

@app.post("/youtube_api/chat_fetch/sw/", tags=["Youtube API"])
def youtube_liveChat_fetch_sw(chat_fecth_sw: bool,background_tasks: BackgroundTasks):
    """
    Youtubeコメントの取得をON_OFFします
    - True : ON
    - False : OFF
    - 事前に'/youtube_api/set_stream_url'を実行し、コメント取得する配信のURLを設定する必要があります。
    """
    if AI_Tuber_setting.youtube_URL == "":
        return {'ok':False,"message": "Stream URL is None"}
    if chat_fecth_sw:
        if AI_Tuber_setting.live_comment_fetch:
            return {'ok':True,"message": "Task is already."}
        AI_Tuber_setting.live_comment_fetch = True
        background_tasks.add_task(youtube_chat_fetch)
        return {'ok':True,"message": "Task started"}
    else:
        AI_Tuber_setting.live_comment_fetch = False
        return {'ok':True,"message": "Task will stop shortly."}
    
@app.get("/youtube_api/chat_fetch/sw-get/", tags=["Youtube API"])
def youtube_liveChat_fetch_sw_get():
    """
    Youtubeコメント取得のON OFF状態を取得
    """
    return AI_Tuber_setting.live_comment_fetch

@app.post("/youtube_api/chat_fetch/post/", tags=["Youtube API"])
def youtube_liveChat_post(comments: dict = {'name': "", 'comment': '','timestamp':None,'superchat_bool':False,'superchat_value':0.0,'superchat_currency':''}):
    """
    配信コメントリストに手動で配列を追加する

    - 'name' (str): コメントの著者の名前。
    - 'comment' (str): コメントのテキスト。
    - 'timestamp' (int): コメントが投稿されたタイムスタンプ。
    - 'superchat_bool' (bool): コメントがスーパーチャットであるかどうか。
    - 'superchat_value' (float): スーパーチャットの金額。
    - 'superchat_currency' (str): スーパーチャットの通貨。
    """
    AI_Tuber_setting.live_comment_list.append(comments)
    return comments

@app.get("/youtube_api/chat_fetch/get/", tags=["Youtube API"])
def youtube_liveChat_get(reset: bool = False):
    """
    配信コメントを配列で取得する

    パラメータ:
    reset: 配列を初期化する

    戻り値:
    - 'name' (str): コメントの著者の名前。
    - 'comment' (str): コメントのテキスト。
    - 'timestamp' (int): コメントが投稿されたタイムスタンプ。
    - 'superchat_bool' (bool): コメントがスーパーチャットであるかどうか。
    - 'superchat_value' (float): スーパーチャットの金額。
    - 'superchat_currency' (str): スーパーチャットの通貨。
    """
    chatlist = AI_Tuber_setting.live_comment_list
    if reset:
        AI_Tuber_setting.live_comment_list = []
    return chatlist

@app.get("/youtube_api/viewer_count/", tags=["Youtube API"])
async def youtube_liveChat_get():
    """
    配信の視聴者数を表示する
    """
    count = await youtube_viewer_count(AI_Tuber_setting.youtube_URL,AI_Tuber_setting.youtube_api_key)
    return count

async def youtube_chat_fetch():
    chat = create_pychat(AI_Tuber_setting.youtube_URL)
    while AI_Tuber_setting.live_comment_fetch:
        new_comments = await youtube_liveChat_fetch(chat=chat)
        if new_comments != []:
            AI_Tuber_setting.live_comment_list.append(new_comments[0])
        await asyncio.sleep(AI_Tuber_setting.interval_s)

async def create_or_load_chroma_db_background():
    AnswerFinder_settings.start = False
    AnswerFinder_settings.finder = AnswerFinder()
    AnswerFinder_settings.finder.create_or_load_chroma_db(AnswerFinder_settings.csv_directory,AnswerFinder_settings.persist_directory)
    AnswerFinder_settings.start = True
        
if __name__ == "__main__":
    #uvicorn API:app --reload   
    import uvicorn
    uvicorn.run("API:app", host="0.0.0.0", port=8001,reload=True)