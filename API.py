
from module.live_chat_fetcher import *
from module.find_similar import AnswerFinder
from module.CSV_toolkit import csv_to_dict_array
from fastapi import FastAPI,BackgroundTasks
from typing import List, Any
import asyncio
import os

app = FastAPI(title='AI Tuber API',version='β1.5')

#将来的にDBに移行
Youtube_comments = []

class mic_setting:
    mic_recording_bool = False

class record_data:
    recorded_list = []

class AI_Tuber_setting:
    AI_talk_bool:bool = False
    interval_s:int = 3
    program_fin = False

class AnswerFinder_settings:
    tone_csv_directory = 'memory/example_tone'
    tone_persist_directory = 'memory/ToneDB'

    motion_csv_directory = 'memory/motion_list/train_data'
    motion_key_csv_file = 'memory/motion_list/motion.csv'
    motion_persist_directory = 'memory/motionDB'
    motion_list = {}

    example_tone_db = None
    motion_db = None

class Youtube_API_settings:
    youtube_api_key = os.getenv("GOOGLE_API_KEY")
    live_comment_fetch:bool = False
    live_comment_list = []
    youtube_URL:str = ""
    youtube_VideoID:str = ""
    youtube_channel_id:str = ""
    youtube_last_comment:dict = {}

class unity_data:
    animation_dict = {}
    unity_logs = []

@app.post("/mic_mute/post/", tags=["Mic Settings"])
def mic_post_item(mic_mute: bool = False):
    """
    マイクの音声認識 ON/OFF:
    - True : OFF
    - False : ON
    """
    mic_setting.mic_recording_bool = mic_mute
    return mic_setting.mic_recording_bool

@app.get("/mic_mute/get/", tags=["Mic Settings"])
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

@app.get("/tone_similar/get/", tags=["Vector Store"])
def tone_similar_get(str_dialogue:str,top_n:int = 3):
    """
    類似会話を検索し、結果を返します
    
    パラメータ:
    str_dialogue: 検索する文字列

    戻り値:
    - レスポンス例 {'text':こんにちわ,'score'"0.22}
    """
    if AnswerFinder_settings.example_tone_db != None:
        result = AnswerFinder_settings.finder.find_similar_vector_store(AnswerFinder_settings.example_tone_db,str_dialogue,top_n)
        

        result.append({'ok':True})
    else:
        result = [{'ok':False,'message':'類似会話検索エンジンが初期化されていません'}]
    return result

@app.get("/tone_similar/start/", tags=["Vector Store"])
def tone_similar_start():
    """
    類似会話検索エンジンを初期化します。
    検索方式はsimilarity searchです。

    注意:
    - 会話例データ: {AnswerFinder_settings.csv_directory}に検索対象のデータが入っている必要があります。
    - Chroma DB: 作成したデータベースは、{AnswerFinder_settings.persist_directory}に保存されます。
    """
    AnswerFinder_settings.example_tone_db = create_or_load_chroma_db_background(AnswerFinder_settings.tone_csv_directory,AnswerFinder_settings.tone_persist_directory)
    return {'ok':True,'message':'tone_similar Start.'}

@app.get("/motion_similar/get/", tags=["Vector Store"])
def motion_similar_get(str_dialogue:str,top_n:int = 3):
    """
    類似モーションを検索し、モーション説明を返します
    
    パラメータ:
    str_dialogue: 検索する文字列

    戻り値:
    - レスポンス例 {'text':こんにちわ,'score'"0.22}
    """
    if AnswerFinder_settings.motion_db != None:
        responce = AnswerFinder_settings.finder.find_similar_vector_store(AnswerFinder_settings.motion_db,str_dialogue,top_n)

        #モーション名を取得する
        motion_dict = csv_to_dict_array(AnswerFinder_settings.motion_key_csv_file,0,1)
        result = []
        for item1 in responce:
            if 'text' in item1:
                print(item1)
                for item2 in motion_dict:
                    print(f"item2: {item2}")
                    if item1['text'] in item2.values():
                        name = list(item2.keys())[0]
                        result.append({
                            "name": name,
                            "text": item1['text'],
                            "score": item1['score']
                        })
                        break
            else:
                result.append(item1)
        #レスポンス結果を追加する
        result.append({'ok':True})
    else:
        result = [{'ok':False,'message':'類似会話検索エンジンが初期化されていません'}]
    return result

@app.get("/motion_similar/start/", tags=["Vector Store"])
def motion_similar_start():
    """
    類似モーション検索エンジンを初期化します。
    検索方式はsimilarity searchです。

    注意:
    - 会話例データ: {AnswerFinder_settings.csv_directory}に検索対象のデータが入っている必要があります。
    - Chroma DB: 作成したデータベースは、{AnswerFinder_settings.persist_directory}に保存されます。
    """
    AnswerFinder_settings.motion_db = create_or_load_chroma_db_background(AnswerFinder_settings.motion_csv_directory,AnswerFinder_settings.motion_persist_directory)
    return {'ok':True,'message':'motion_similar Start.'}

@app.post("/Program_Fin_bool/post/", tags=["AI Tuber"])
def Program_Fin_post_item(Program_Fin: bool = False):
    """
    プログラムを終了する
    - True : プログラムを終了させます
    """
    AI_Tuber_setting.program_fin = Program_Fin
    return AI_Tuber_setting.program_fin

@app.get("/Program_Fin_bool/get/", tags=["AI Tuber"])
def Program_Fin_get_item():
    """
    プログラム終了関数を取得
    """
    return AI_Tuber_setting.program_fin

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
    Youtube_API_settings.youtube_URL = url
    Youtube_API_settings.youtube_VideoID = extract_video_id(url)
    Youtube_API_settings.youtube_channel_id = get_channel_id(url,Youtube_API_settings.youtube_api_key)
    return {'ok':True,"message": f"URL:{url} / Channel_ID:{Youtube_API_settings.youtube_channel_id}"}

@app.get("/youtube_api/get_stream_url/", tags=["Youtube API"])
def get_stream_url():
    """
    Youtubeコメント取得先URLを取得
    """
    return Youtube_API_settings.youtube_URL

@app.post("/youtube_api/chat_fetch/sw/", tags=["Youtube API"])
def youtube_liveChat_fetch_sw(chat_fecth_sw: bool=False):
    """
    Youtubeコメントの取得をON_OFFします
    - True : ON
    - False : OFF
    - 事前に'/youtube_api/set_stream_url'を実行し、コメント取得する配信のURLを設定する必要があります。
    """
    if Youtube_API_settings.youtube_URL == "":
        return {'ok':False,"message": "Stream URL is None"}
    if chat_fecth_sw:
        if Youtube_API_settings.live_comment_fetch:
            return {'ok':True,"message": "Task is already."}
        Youtube_API_settings.live_comment_fetch = True

        #最後のコメントを取得しておく
        comment_list = get_new_comments(Youtube_API_settings.youtube_VideoID,Youtube_API_settings.youtube_api_key)
        Youtube_API_settings.youtube_last_comment = comment_list[-1]

        return {'ok':True,"message": "Task started"}
    else:
        Youtube_API_settings.live_comment_fetch = False
        return {'ok':True,"message": "Task will stop shortly."}
    
@app.get("/youtube_api/chat_fetch/sw-get/", tags=["Youtube API"])
def youtube_liveChat_fetch_sw_get():
    """
    Youtubeコメント取得のON OFF状態を取得
    """
    return Youtube_API_settings.live_comment_fetch

@app.get("/youtube_api/chat_fetch/get/", tags=["Youtube API"])
def youtube_liveChat_get():
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
    if Youtube_API_settings.live_comment_fetch == False:
        return {'ok':False,'message':'Chat FetchがONになっていません。'}
    
    chatlist = get_new_comments(Youtube_API_settings.youtube_VideoID,Youtube_API_settings.youtube_api_key)
    matching_data_and_after = []
    found_match = False
    if chatlist != []:
        for d in chatlist:
            if found_match:
                # 一致した後のデータをリストに追加
                matching_data_and_after.append(d)
            elif d == Youtube_API_settings.youtube_last_comment:
                # 一致するデータを見つけたらフラグを立て、リストに追加
                found_match = True
        if matching_data_and_after == []:
            matching_data_and_after = chatlist
    Youtube_API_settings.youtube_last_comment = chatlist[-1]
    return matching_data_and_after

@app.get("/youtube_api/viewer_count/", tags=["Youtube API"])
async def youtube_viewer_count_get():
    """
    配信の視聴者数を表示する
    """
    if Youtube_API_settings.youtube_URL != "":
        count = await youtube_viewer_count(Youtube_API_settings.youtube_URL,Youtube_API_settings.youtube_api_key)
        return count
    else:
        return {'ok':False,"message": "Stream URL is None"}

@app.get("/youtube_api/subscriber_count/", tags=["Youtube API"])
async def youtube_subscriber_count_get():
    """
    チャンネル登録者数を取得する
    """
    if Youtube_API_settings.youtube_channel_id != "":
        count = await youtube_subscriber_count(Youtube_API_settings.youtube_channel_id,Youtube_API_settings.youtube_api_key)
        return count
    else:
        return {'ok':False,"message": "Stream URL is None"}
    
@app.post("/Unity/animation/post/", tags=["Unity"])
def Unity_animation_dict_post(U_anim_dict: dict):
    """
    Unity Animation Dictに関数を追加します。
    Unity Animation DictはAPI→Unityに通信する関数です
    
    パラメータ:
    - VRM_expression: 表情設定をする関数です
        - Neutral
        - Angry
        - Fun
        - Joy
        - Sorrow
        - Surprised みらいアバターでは動作せず
        - LookUp
        - LookDown
        - LookLeft
        - LookRight
        - A
        - I
        - U
        - E
        - O
        - Blink
        - Blink_L
        - Blink_R
    - VRM_animation: animアニメーション名設定する関数です
    - SnapshotAnimationFrames: アニメーションスクリーンショットを実行する関数
        - true
        - flase
    - SetSnapshotCount: 撮影枚数を設定する関数
        - 1-100...

    """
    # 受け取った辞書の内容を検証する
    if not U_anim_dict:
        return {'ok':False,"message": "Empty dictionary received"}
    unity_data.animation_dict.update(U_anim_dict)
    return {'ok':True,"message": "Animation data processed successfully"}

@app.get("/Unity/animation/get/", tags=["Unity"])
def Unity_animation_dict_get(reset: bool = False):
    """
    Unity Animation Dictに関数の内容を取得します。
    """
    responce = unity_data.animation_dict
    if reset:
        unity_data.animation_dict = {}
    return responce

@app.get("/Unity/animation/list/get", tags=["Unity"])
def Unity_animation_list_get():
    """
    利用可能なUnity Animation を一覧で取得します
    """
    return csv_to_dict_array(AnswerFinder_settings.motion_key_csv_file,0,1)

@app.post("/Unity/log/post/", tags=["Unity"])
def Post_Unity_Logs(logs: dict):
    """
    Unity Logにデータを追加します。Unity Logはリスト配列です。

    """
    print(logs)
    # 受け取った辞書の内容を検証する
    if logs == {}:
        return{'ok':False,"message": "Empty dictionary received"}
    unity_data.unity_logs.append(logs)
    return {'ok':True,"message": "log data processed successfully"}

@app.get("/Unity/log/get/", tags=["Unity"])
def get_Unity_Logs(reset: bool = False):
    """
    Unity Logのデータを参照します
    """
    responce = unity_data.unity_logs
    if reset:
        unity_data.unity_logs = []
    return responce

def create_or_load_chroma_db_background(csv_directory,persist_directory):
    AnswerFinder_settings.start = False
    AnswerFinder_settings.finder = AnswerFinder()
    database = AnswerFinder_settings.finder.create_or_load_chroma_db(csv_directory,persist_directory)
    return database
        
if __name__ == "__main__":
    #uvicorn API:app --reload   
    import uvicorn
    uvicorn.run("API:app", host="0.0.0.0", port=8001,reload=True)