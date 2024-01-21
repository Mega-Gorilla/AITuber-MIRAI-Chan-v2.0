
from module.live_chat_fetcher import *
from module.find_similar import AnswerFinder
from module.CSV_toolkit import csv_to_dict_array
from module.cloud_vision import *
from module.screenshot import *
from module.voicevox import *
from module.auto_key import *
from rich.console import Console
from fastapi import FastAPI,BackgroundTasks,HTTPException,Request
from fastapi.responses import JSONResponse
from typing import List, Any, Dict
from pydantic import BaseModel
import asyncio
import os
import json

console = Console()
app = FastAPI(title='AI Tuber API',version='β1.5')

#将来的にDBに移行
Youtube_comments = []

class mic_setting:
    mic_recording_bool = False
    processing = False

class record_data:
    recorded_list = []

class AI_Tuber_setting:
    AI_talk_bool:bool = False
    interval_s:int = 3
    program_fin = False
    Showrunner_advice_prompt_name = ""
    talk_log = []
    summary_str = "None"
    summary_process = False
    summary_game_process = False

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

class ocr:
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] ="D:\\GoogleDrive\\solo\\key\\ai-tuber-api-dc0b1b81cad7.json"
    AutoTextScroll = False

class OCRResult(BaseModel):
    coordinates: List[List[int]]
    text: str
    confidence: float

class game_data:
    Game_info_path = "data/game_info"
    Game_talkLog= []
    Game_name = ""
    summary_str = "None"

class LLM_config:
    request_list = []
    process_list = []

class text_to_vice_data:
    voice_requests = []

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # ここでエラーの詳細をprint
    print(f"エラー詳細: {exc.detail}")
    return {"ok":False,'message':JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})}

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

@app.post("/StoT_process/post/", tags=["Mic Settings"])
def mic_post_item(process: bool = False):
    """
    音声を文字化している:
    - True : 文字化中
    - False : 文字化終了
    """
    mic_setting.processing = process
    return mic_setting.processing

@app.get("/StoT_process/get/", tags=["Mic Settings"])
def mic_get_item():
    """
    Voice To Text実行状況取得
    """
    return mic_setting.processing

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

@app.get("/Showrunner_Advice_list/get/", tags=["AI Tuber"])
def Showrunner_advice_get():
    """
    Showrunner_advice プロンプトのリストを取得する
    """
    try:
        with open('data/showrunner_advice_list.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="[data/showrunner_advice_list.json] not found.")
    except json.JSONDecodeError:
        raise HTTPException(status_code=404, detail="Error decoding JSON.")

@app.post("/Showrunner_Advice/post/", tags=["AI Tuber"])
def Showrunner_advice_post(prompt_name:str="",mic_end: bool =False,AI_talk:bool = False):
    """
    Showrunner_advice プロンプトを内容を取得する
    - prompt_name: 内容を取得するプロンプト名を設定する
    - 注意:最後に呼び出されたプロンプト名は記憶され、prompt_name=""で参照された際、最後に呼び出されたプロンプト内容を返します

    - mic_end: プロンプト内容取得後、マイク聞き取りを終了する場合はTrueに設定してください
    """
    if prompt_name == "":
        if AI_Tuber_setting.Showrunner_advice_prompt_name !="":
            prompt_name = AI_Tuber_setting.Showrunner_advice_prompt_name
        else:
            raise HTTPException(status_code=403, detail="Prompt_name Error")
    else:
        AI_Tuber_setting.Showrunner_advice_prompt_name = prompt_name
    
    if mic_end:
        if mic_setting.mic_recording_bool == False:
            mic_setting.mic_recording_bool = True
            mic_setting.processing = True
    
    try:
        with open('data/showrunner_advice_list.json', 'r', encoding='utf-8') as file:
            data = json.load(file)

            if AI_talk:
                AI_Tuber_setting.AI_talk_bool = True
            
            return data.get(prompt_name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found.")
    except json.JSONDecodeError:
        raise HTTPException(status_code=404, detail="Error decoding JSON.")
    
@app.post("/LLM/request/post/", tags=["LLM"])
def LLM_request_post(prompt_name:str,stream:bool,variables:dict=None,):
    """
    LLMへの、問合せ要望をします
    """
    print("-------------------------------------")
    print()
    LLM_config.request_list.append({"prompt_name":prompt_name,"variables":variables,"stream":stream})
    return {'ok':True}

@app.get("/LLM/request/get/", tags=["LLM"])
def LLM_request_get(reset:bool=False):
    """
    LLMへの問合せ要望を取得します
    """
    result = LLM_config.request_list
    if reset:
        LLM_config.request_list = []
    return result

@app.post("/LLM/process/post/", tags=["LLM"])
def LLM_process_post(request_id:str,prompt_name:str,stream:bool):
    """
    LLMから出力された結果の処理要望を行います
    """
    LLM_config.process_list.append({"request_id":request_id,"prompt_name":prompt_name,"stream":stream})
    return {'ok':True}

@app.get("/LLM/process/get/", tags=["LLM"])
def LLM_process_get(del_request_id:str=None):
    """
    LLMから出力された結果の処理要望を取得します
    """
    result = LLM_config.process_list
    if del_request_id != None:
        LLM_config.process_list = [d for d in LLM_config.process_list if d['request_id'] != del_request_id]
    return result

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


@app.post("/talk_log/post",tags=["AI Tuber"])
def post_talk_log(talklog_list: List[Dict[str, str]]):
    """
    トークログを投稿します
    """
    print(f"Talk_log: {talklog_list}")
    AI_Tuber_setting.talk_log+=talklog_list
    return AI_Tuber_setting.talk_log

@app.get("/talk_log/get",tags=["AI Tuber"])
def get_talk_log(reset:bool = False):
    """
    トークログを取得します
    """
    return_data = AI_Tuber_setting.talk_log
    if reset:
        AI_Tuber_setting.talk_log = []
    return return_data

class SummaryModel(BaseModel):
    summary: str

@app.post("/summary/post",tags=["AI Tuber"])
def post_summary(summary_data: SummaryModel):
    """
    サマリーを投稿します
    """
    summary = summary_data.summary
    print(f"Summary: {summary}")
    AI_Tuber_setting.summary_str = summary
    return {"summary": AI_Tuber_setting.summary_str}

@app.get("/summary/get",tags=["AI Tuber"])
def get_summary():
    """
    サマリーを取得します
    """
    return_data = AI_Tuber_setting.summary_str
    return return_data

@app.post("/summary_process/post/", tags=["AI Tuber"])
def mic_post_item(summary_process: bool = None,summray_game_process:bool =None):
    """
    要約実行中 ON/OFF:
    - True : 要約中
    - False : 要約終了
    """
    if summary_process != None:
        AI_Tuber_setting.summary_process = summary_process
    if summray_game_process != None:
        AI_Tuber_setting.summary_game_process = summray_game_process
    return {'summary_talk':summary_process,'summary_game':summray_game_process}

@app.get("/summary_process/get/", tags=["AI Tuber"])
def mic_get_item():
    """
    要約状態確認
    """
    return {'summary_talk':AI_Tuber_setting.summary_process,'summary_game':AI_Tuber_setting.summary_game_process}

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
    channel_id = get_channel_id(url,Youtube_API_settings.youtube_api_key)
    if channel_id != False:
        Youtube_API_settings.youtube_channel_id = get_channel_id(url,Youtube_API_settings.youtube_api_key)
        return {'ok':True,"message": f"URL:{url} / Channel_ID:{Youtube_API_settings.youtube_channel_id}"}
    else:
        return {'ok':False}

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

@app.post("/OCR/scan/",tags=["OCR"])
def ocr_scan(screen_num: int,capture_size: List[int] = [],save_image: str = "",white_black_filter:bool=True):
    """
    OCR スキャンを行います
    
    パラメータ:
    - screen_num: スクリーンショットを撮影するディスプレイ番号を設定する。例:1
    - capture_size: スキャンする画面座標を指定します。例:[800, 1550, 3000, 2000]
    - save_image: スキャンした画像を保存する場合、パスを入力します。
    - white_black_fliter: 白以外の色のをすべて黒色に塗りつぶすフィルターをON/OFFします。
    """
    if len(capture_size) != 4:
        raise HTTPException(status_code=400, detail="Invalid capture size. List must contain exactly 3 elements.")
    
    monitor_number = screen_num 
    screenshot = take_screenshot(monitor_number)
    if screenshot['ok']:
        screenshot = screenshot['img']
    else:
        raise HTTPException(status_code=400, detail=screenshot['Error'])
    if capture_size != []:
        cropped_screenshot = crop_image(screenshot, capture_size)
        cropped_screenshot = screenshot
    if white_black_filter:
        cropped_screenshot = fill_non_white_pixels_black(cropped_screenshot)
    if save_image != "":
        save_path = f"{save_image}/cropped_monitor_{monitor_number}.png"
        save_image(cropped_screenshot, save_path)
    ocr_texts = cloud_vision_OCR(cropped_screenshot)
    return ocr_texts

class dokidoki_voice_config:
    # No.7,九州そら,猫使ビィ,四国めたん,青山龍星,ずんだもん
    chara_list = [{
        "chara_name": "ユリ",
        "speaker_uuid": "044830d2-f23b-44d6-ac0d-b5d733caa900",
        "style_id": 29,
        "speedScale": 1.1,
        "pitchScale": 0,
        "intonationScale": 1.2,
        "volumeScale": 1.2,
        "prePhonemeLength": 0.1,
        "postPhonemeLength": 0.1
        },
        {
        "chara_name": "モニカ",
        "speaker_uuid": "481fb609-6446-4870-9f46-90c4dd623403",
        "style_id": 17,
        "speedScale": 1.3,
        "pitchScale": 0.05,
        "intonationScale": 1.2,
        "volumeScale": 1.0,
        "prePhonemeLength": 0.1,
        "postPhonemeLength": 0.1
        },
        {
        "chara_name": "サヨリ",
        "speaker_uuid": "c20a2254-0349-4470-9fc8-e5c0f8cf3404",
        "style_id": 58,
        "speedScale": 1.2,
        "pitchScale": -0.03,
        "intonationScale": 1.2,
        "volumeScale": 1.0,
        "prePhonemeLength": 0.1,
        "postPhonemeLength": 0.1
        },
        {
        "chara_name": "ナツキ",
        "speaker_uuid": "7ffcb7ce-00ec-4bdc-82cd-45a8889e43ff",
        "style_id": 2,
        "speedScale": 1.2,
        "pitchScale": 0.03,
        "intonationScale": 1.31,
        "volumeScale": 1.0,
        "prePhonemeLength": 0.1,
        "postPhonemeLength": 0.1
        },
        {
        "chara_name": "ハカセ",
        "speaker_uuid": "4f51116a-d9ee-4516-925d-21f183e2afad",
        "style_id": 13,
        "speedScale": 1.2,
        "pitchScale": 0.0,
        "intonationScale": 1.0,
        "volumeScale": 1.0,
        "prePhonemeLength": 0.1,
        "postPhonemeLength": 0.1
        },
        {
        "chara_name": "読み上げ",
        "speaker_uuid": "388f246b-8c41-4ac1-8e2d-5d79f3ff56d9",
        "style_id": 3,
        "speedScale": 1.2,
        "pitchScale": 0.0,
        "intonationScale": 1.0,
        "volumeScale": 1.0,
        "prePhonemeLength": 0.1,
        "postPhonemeLength": 0.1
        }]

def parse_text(input_text):
    # 会話文かどうかを判定するためのフラグ
    if "「" in input_text and "」" in input_text:
        # キャラクター名と会話文を分割
        parts = input_text.split('\n', 1)
        name = parts[0].strip()
        text = parts[1].strip()
    else:
        # 会話文でない場合はナレーションとして扱う
        name = "narration"
        text = input_text.strip()
    
    # 結果を辞書で返す
    return {"name": name, "text": text}

@app.post("/test")
def test():
    send_key_to_app("Doki Doki Literature Club!", "space")

@app.post("/OCR/scan/Doki_Doki_Literature_Club/",tags=["OCR"])
async def Doki_Doki_Literature_Club_ocr(AutoVoice:bool = False,AutoScroll:int =1):
    """
    OCR スキャンを行います。このスキャンは、Doki Doki Literature Clubに対応しています。
    OCR結果を返します。スキャンしたOCR結果は、game_data.Game_talkLogに記録されます。

    パラメータ:
    """
    for i in range(AutoScroll):
        #スペースキーを挿入
        send_key_to_app("Doki Doki Literature Club!", "space")
        await asyncio.sleep(0.5)
        monitor_number = 1 
        screenshot = take_screenshot(monitor_number)
        if screenshot['ok']:
            screenshot = screenshot['img']
        else:
            raise HTTPException(status_code=400, detail=screenshot['Error'])
        
        crop_area = (725, 1555, 3050, 2100)  
        cropped_screenshot = crop_image(screenshot, crop_area)
        cropped_screenshot = fill_non_white_pixels_black(cropped_screenshot)
        ocr_texts = cloud_vision_OCR(cropped_screenshot)
        parsed_text = parse_text(ocr_texts)#文章を辞書配列に変換
        game_data.Game_talkLog.append(parsed_text)

        if AutoVoice:
            matching_chara_dict = next((item for item in dokidoki_voice_config.chara_list if item["chara_name"] == parsed_text['name']), dokidoki_voice_config.chara_list[-1])
            matching_chara_dict.update({"text": parsed_text["text"],"subs": False,"service":'voicevox','lipsync':False})
            text_to_vice_data.voice_requests.append(matching_chara_dict)
            while True:
                if text_to_vice_data.voice_requests==[]:
                    break
                await asyncio.sleep(1)
    return parsed_text

@app.get("/GameData/talk_log/get",tags=["Games"])
def get_game_talk_log(reset:bool = False):
    """
    ゲームトークログを取得します
    """
    return_data = game_data.Game_talkLog
    if reset:
        game_data.Game_talkLog = []
    return return_data

class GameTalkLog(BaseModel):
    name: str
    text: str

@app.post("/GameData/talk_log/post",tags=["Games"])
def post_game_talk_log(gamelog: List[GameTalkLog]):
    """
    ゲームトークログを投稿します
    """
    print(f"GameLog: {gamelog}")
    game_data.Game_talkLog+=gamelog
    return game_data.Game_talkLog

@app.post("/GameData/summary/post",tags=["Games"])
def post_game_summary(summary_data: SummaryModel):
    """
    サマリーを投稿します
    """
    summary = summary_data.summary
    print(f"GameSummary: {summary}")
    game_data.summary_str = summary
    return {"summary": AI_Tuber_setting.summary_str}

@app.get("/GameData/summary/get",tags=["Games"])
def get_game_summary():
    """
    サマリーを取得します
    """
    return_data = game_data.summary_str
    return return_data

@app.get("/GameData/GameInfo/get",tags=["Games"])
def get_game_info(game_name: str = ""):
    """
    data/game_infoにあるtxtファイルデータを取得して返します。
    """
    if game_name == "" and game_data.Game_name != "":
        game_name =  game_data.Game_name
    elif game_name == "":
        raise HTTPException(status_code=404, detail="Nothings GameName. Please set Game Name")
    texts = ""
    text_files_found = False
    folder_path = game_data.Game_info_path
    filename = f"{game_name}.txt"

    # フォルダが存在するかチェック
    if not os.path.exists(folder_path):
        raise HTTPException(status_code=404, detail="Folder Not found.")

    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            text_files_found = True
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                texts = file.read()

    # テキストファイルが一つも見つからなかった場合のエラーメッセージ
    if not text_files_found:
        raise HTTPException(status_code=404, detail="txtfile Not found.")

    return texts

@app.get("/GameList/get", tags=["Games"])
def get_game_info():
    """
    data/game_infoにあるtxtファイル名のリストを取得して返します（.txt拡張子は除く）。
    """
    folder_path = game_data.Game_info_path
    txt_files = []

    # フォルダが存在するかチェック
    if not os.path.exists(folder_path):
        raise HTTPException(status_code=404, detail="Folder Not found.")

    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            # .txt拡張子を除去してリストに追加
            txt_files.append(filename.rstrip('.txt'))

    # テキストファイルが一つも見つからなかった場合のエラーメッセージ
    if not txt_files:
        raise HTTPException(status_code=404, detail="txtfile Not found.")

    return txt_files

@app.post("/GameName/set", tags=["Games"])
def set_game_name(game_name:str = ""):

    folder_path = game_data.Game_info_path
    txt_files = []

    # フォルダが存在するかチェック
    if not os.path.exists(folder_path):
        raise HTTPException(status_code=404, detail="Folder Not found.")

    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            # .txt拡張子を除去してリストに追加
            txt_files.append(filename.rstrip('.txt'))

    # テキストファイルが一つも見つからなかった場合のエラーメッセージ
    if not txt_files:
        raise HTTPException(status_code=404, detail="txtfile Not found.")
    if game_name in txt_files or game_name == "":
        game_data.Game_name = game_name
        return game_name
    else:
        raise HTTPException(status_code=404, detail="Game info Data Not found.")
    
@app.get("/GameName/get", tags=["Games"])
def get_game_name():
    return game_data.Game_name

class voicevox_request(BaseModel):
    chara_name: str
    text: str
    subs: bool = True
    lipsync: bool = True
    speaker_uuid: str = ""
    style_id: int = 0
    speedScale : float = 1.0
    pitchScale : float = 0.0
    intonationScale : float = 1.0
    volumeScale : float = 1.0
    prePhonemeLength : float = 0.1
    postPhonemeLength : float = 0.1
    
@app.post("/text_to_vice/voicevox/post",tags=['Text to Voice'])
def text_to_voice_post(post_data:voicevox_request):
    data = post_data.dict()
    data.update({'service':'voicevox'})
    text_to_vice_data.voice_requests.append(data)
    return text_to_vice_data.voice_requests

@app.post("/text_to_vice/get", tags=['Text to Voice'])
def text_to_voice_get(reset: dict = {}):
    data = text_to_vice_data.voice_requests
    if reset != {}:
        # reset リスト内の各要素に対して、voice_requests 内のデータを削除
        text_to_vice_data.voice_requests = [item for item in text_to_vice_data.voice_requests if item != reset]
    return data

def create_or_load_chroma_db_background(csv_directory,persist_directory):
    AnswerFinder_settings.start = False
    AnswerFinder_settings.finder = AnswerFinder()
    database = AnswerFinder_settings.finder.create_or_load_chroma_db(csv_directory,persist_directory)
    return database
        
if __name__ == "__main__":
    #uvicorn API:app --reload   
    import uvicorn
    uvicorn.run("API:app", host="0.0.0.0", port=8001,reload=True)