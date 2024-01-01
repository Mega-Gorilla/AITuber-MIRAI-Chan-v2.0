
from module.rich_desgin import error,warning_message
from module.server_requests import *
from module.fast_whisper import *
from module.deepl import atranslate_text
from module.voicevox import *
from module.youtube_api import *
from module.LLM_Process import *
from module.LLM_Request import *
from rich import print
from rich.console import Console
import multiprocessing
import time
import asyncio
import os
import json
import random

class config:
    #URL
    GPT_Mangaer_URL = "http://127.0.0.1:8000"
    AI_Tuber_URL = "http://127.0.0.1:8001"

    #みらい1.5 プロンプト
    mirai_prompt_name = 'airi_v17'
    viewer_count = 0
    subscriber_count = 0

    #監督　プロンプト
    charactor_list = """未来 アイリ
猩々 博士"""
    facial_expressions_list = """NEUTRAL (This is the default expression)
Joy
Angry
Fun"""
    director_list = []

    #VoiceVox
    voicevox_name = 'AIRI'
    speaker_uuid = "9f3ee141-26ad-437e-97bd-d22298d02ad2"
    style_id = 20
    voicevox_save_path = 'voice_data'

    requestList = {}
    
    total_token = 0

    AI_gesture_emotion_state_list = []
    VoiceVox_list = []
    motion_list = []
    translatedict = {}

class LLM_config:
    #プロンプトごとの呼び出す関数を選択
    request_function_map = {
        "talk_logTosummary":request_talk_logTosummary,
        "game_logTosummary":request_game_logTosummary,
        "airi_v17":request_airi_v17_2,
        "airi_v17_gemini":request_airi_v17_gemini
        }
    process_function_map = {
        "airi_v17": process_airi_v17,
        "airi_v17_gemini":process_airi_v17,
        "talk_logTosummary":process_talk_logTosummary,
        "game_logTosummary":process_game_logTosummary,
        "Statement_to_animMotion_2":Statement_to_animMotion,
        }

console = Console()
        
async def youtube_counter_initialize():
    viewer_count = await get_youtube_viewer_counts()
    if "viewer_count" in viewer_count:
        config.viewer_count = viewer_count['viewer_count']
    subscriber_count = await get_youtube_subscriber_counts()
    if "subscriber_count" in subscriber_count:
        config.subscriber_count = subscriber_count['subscriber_count']

async def youtube_API_Check():
    commnet_url = requests.get(f"{config.AI_Tuber_URL}/youtube_api/get_stream_url/").json()
    if commnet_url == "":
        warning_message("Stream URLが設定されていません。Youtube APIが利用できません!")
    else:
        await youtube_counter_initialize()
        # コメント取得開始
        await post_data_from_server(f"{config.AI_Tuber_URL}/youtube_api/chat_fetch/sw/?chat_fecth_sw=true")

async def get_mic_recorded_str():
    mic_recorded_list = requests.get(f"{config.AI_Tuber_URL}/mic_recorded_list/get/?reset=true").json()
    if mic_recorded_list == []:
        result = ""
    else:
        result = '\n'.join([' '.join(item) for item in mic_recorded_list])
    return result

async def request_llm(prompt_name,variables,stream=False):
    current_time = int(time.time() * 1000)
    request_id = str(current_time)
    
    requests.post(f"{config.GPT_Mangaer_URL}/LLM/request/?prompt_name={prompt_name}&request_id={request_id}&stream_mode={stream}",json={"variables" : variables})
    requests.post(f"{config.AI_Tuber_URL}/LLM/process/post/?request_id={request_id}&prompt_name={prompt_name}&stream={stream}")
    console.print("\n------------------Prompt Data------------------",style='blue')
    console.print(prompt_name,style='yellow')
    for key,value in variables.items():
        console.print(f"{key}: {value}",style='green')
    console.print("------------------END------------------\n",style='blue')

    return request_id

async def reset_similarity_search():
    #類似検索を初期化する
    print(await get_data_from_server(f"{config.AI_Tuber_URL}/tone_similar/start/")) #類似検索を初期化
    await asyncio.sleep(0)
    print(await get_data_from_server(f"{config.AI_Tuber_URL}/motion_similar/start/")) #類似検索を初期化
    await asyncio.sleep(0)

def process1_function():
    #マイク音声聞き取り＋文字化
    speech_to_text = AudioProcessor()
    try:
        while requests.get(f"{config.AI_Tuber_URL}/Program_Fin_bool/get/").text.lower() == 'false': #プログラム実行状況を確認
            response = requests.get(f"{config.AI_Tuber_URL}/mic_mute/get/")     #マイク録音状態の確認

            # マイク録音開始の場合。
            if response.text.lower() == 'false':          
                requests.post(url=f"{config.AI_Tuber_URL}/StoT_process/post/",json=True) 
                speech_to_text.process_stream()
                print('mic end.')
                speech_to_text.stop()
                # 終了時にバッファをファイルに保存
                speech_to_text.save_buffer_to_file('output.wav')
                speech_to_text.reset()
                speech_to_text.start()
                
                #録音音声データを文字化する
                text_data_list = speech_to_text.transcribe('output.wav',False)
                speech_to_text.close()

                #マイク文字列データをポスト
                requests.post(
                    f'{config.AI_Tuber_URL}/mic_recorded_list/post/',
                    json=text_data_list
                )
                print("文字化完了")
                requests.post(url=f"{config.AI_Tuber_URL}/StoT_process/post/",json=False)
            
            else:
                if os.path.isfile(config.voicevox_save_path) and config.voicevox_save_path.endswith('.wav'):
                    pass
                time.sleep(1)
            
    except Exception as e:
        # ここでエラーを処理する
        print(f"予期せぬエラーが発生しました: {e}")
    finally:
        speech_to_text.close()

async def Mirai_15_model():
    # 会話検索エンジンの初期化
    print("初期化中...")
    await reset_similarity_search() #類似検索の初期化
    requests.get(f"{config.GPT_Mangaer_URL}/LLM/get/?reset=true")
    Add_preset(1,config.voicevox_name,config.speaker_uuid,config.style_id) #ViceVoxの初期化
    print("初期化完了")

    # YoutubeAPIが設定されているか確認
    await youtube_API_Check()
    
    while requests.get(url=f"{config.AI_Tuber_URL}/Program_Fin_bool/get/").json() == False:
        mirai_talkSW = requests.get(url=f"{config.AI_Tuber_URL}/AI_talk_bool/get/").json()

        if mirai_talkSW:
            #---------------------------------- AIトークボタンを押したときの処理 ----------------------------------
            requests.post(f"{config.AI_Tuber_URL}/AI_talk_bool/post/",json={'AI_talk': False})#問合せフラグをFalseに

            # アイリ向けプロンプト問い合わせをリクエストする
            while True:
                #Voice To Textが終わるまで待つ
                result = requests.get(url=f"{config.AI_Tuber_URL}/StoT_process/get/").json()
                if result == False:
                    break
                await asyncio.sleep(0.2)
            #LLM問合せリクエスト
            requests.post(f"{config.AI_Tuber_URL}/LLM/request/post/?prompt_name={config.mirai_prompt_name}&stream=true")

        else:
            #---------------------------------- AI Talkボタンが押されていないときの処理 -------------------------------
            #-------- LLMへのリクエストリストを処理する
            #request_list = await get_data_from_server(f"{config.AI_Tuber_URL}/LLM/request/get/?reset=true")
            request_list = requests.get(url=f"{config.AI_Tuber_URL}/LLM/request/get/?reset=true").json()
            if len(request_list) != 0:
                try:
                    for item in request_list:
                        if 'variables' in item and item['variables']!=None:
                            #すでに変数が代入されているものはリクエストに追加。
                            await request_llm(prompt_name=item['prompt_name'],variables=item['variables'],stream=item['stream'])
                        else:
                            #変数が代入されていない場合は、変数問合せ実行
                            variables = await LLM_config.request_function_map[item['prompt_name']]()
                            await request_llm(prompt_name=item['prompt_name'],variables=variables,stream=item['stream'])
                except Exception as e:
                    error("LLM リクエストエラー",e,{'request_list':request_list,'item':item})

            #-------- LLMへのプロセスリストを処理する
            process_list = requests.get(url=f"{config.AI_Tuber_URL}/LLM/process/get/").json()
            if len(process_list) == 0:
                #LLMリクエスト行われていないときはループ無視
                await asyncio.sleep(1)
                continue

            #タスクを追加する
            stream_true = [item for item in process_list if item["stream"]]
            stream_false = [item for item in process_list if not item["stream"]]

            #Streamタスクについては即時タスク化
            for request in stream_true:
                asyncio.create_task(LLM_config.process_function_map[request["prompt_name"]](request["request_id"]))
                requests.get(f"{config.AI_Tuber_URL}/LLM/process/get/?del_request_id={request['request_id']}")
                await asyncio.sleep(0)

            #通常問い合わせタスクについては、返答が返ってきているもののみタスク化
            try:
                LLM_results_list = requests.get(f"{config.GPT_Mangaer_URL}/LLM/get/?reset=false").json() #LLM結果の取得
                if LLM_results_list == []:
                    await asyncio.sleep(1)
                    continue
                LLM_results_request_id_list = {d["request_id"] for d in LLM_results_list} #"request_idデータのみを抜き出し"
                stream_false = [d for d in stream_false if d["request_id"] in LLM_results_request_id_list] #stream_falseよりレスポンスが返ってきていないものを消去
            except Exception as e:
                error("Process タスク作成エラー",e,{"stream":False,"LLM_results_list":LLM_results_list,"LLM_results_request_id_list":LLM_results_request_id_list,"stream_false":stream_false})
            #LLMからレスポンスが返ってきているものについてはProcessタスクを実行する。
            for request in  stream_false:
                asyncio.create_task(LLM_config.process_function_map[request["prompt_name"]](request["request_id"]))
                requests.get(f"{config.AI_Tuber_URL}/LLM/process/get/?del_request_id={request['request_id']}")
                await asyncio.sleep(0)
            
            await asyncio.sleep(1)

def process2_function():
    asyncio.run(Mirai_15_model())

if __name__ == "__main__":
    
    requests.post(f"{config.AI_Tuber_URL}/Program_Fin_bool/post/?Program_Fin=false")

    #multiprocessing用プロセス作成
    process1 = multiprocessing.Process(target=process1_function)
    process2 = multiprocessing.Process(target=process2_function)

    #multiprocessingプロセス開始
    process1.start()
    process2.start()

    process1.join()
    process2.join()