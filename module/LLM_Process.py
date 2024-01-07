import requests,asyncio
from module.voicevox import *
from module.LLM_Request import summary_data
from rich.console import Console
from module.rich_desgin import error,warning_message
import time

"""
本スクリプトは、LLM問合せ後の処理がプロンプトごとに記載されています。
どのプロンプトに対してどの関数が対応しているかは、main.py LLM_config.function_mapを参照のこと
"""
console = Console()
 
class config:
    #URL
    GPT_Mangaer_URL = "http://127.0.0.1:8000"
    AI_Tuber_URL = "http://127.0.0.1:8001"
    talker = "voicevox"
    
    motion_list_top_n = 4

class LLM:
    total_token_summary_trigger = {"gpt-4-1106-preview":3171,"gpt-4":6143} #"gpt-4-1106-preview":3171,"gpt-4":6143
    completion_token_summary_trigger = {"gemini-pro":6144}

    loop_break_time = 60 #s

class voicevox_config:
    # 一時的、VoiceVox移行後消去
    voicevox_name = 'AIRI'
    speaker_uuid = "9f3ee141-26ad-437e-97bd-d22298d02ad2"
    style_id = 20
    parameters = [{'name':'neutral','Speaking_Speed':1.2,'Voice_Pitch':0,'Voice_Intonation':1,'volumeScale':1},
                 {'name':'anger','Speaking_Speed':1.2,'Voice_Pitch':-0.05,'Voice_Intonation':0.8,'volumeScale':1},
                 {'name':'disgust','Speaking_Speed':1.2,'Voice_Pitch':-0.1,'Voice_Intonation':0.6,'volumeScale':1},
                 {'name':'fear','Speaking_Speed':1.4,'Voice_Pitch':0.08,'Voice_Intonation':1.2,'volumeScale':1},
                 {'name':'happy','Speaking_Speed':1.2,'Voice_Pitch':0.05,'Voice_Intonation':1.5,'volumeScale':1},
                 {'name':'sad','Speaking_Speed':0.9,'Voice_Pitch':0.09,'Voice_Intonation':1.3,'volumeScale':1},
                 {'name':'surprise','Speaking_Speed':1.2,'Voice_Pitch':0.05,'Voice_Intonation':1.1,'volumeScale':1}]

async def process_airi_v17(request_id):
    """
    アイリ v17向け処理関数
    Streamのみ対応
    """
    process_airi_v17_start_time = time.time()
    content = ""
    done = False
    #切り取りマーカーリスト
    markers = [["# Organize Your  Thoughts:","#Result:"],["# Organize Your Thoughts:","# Result:"],["emotion:","facial expression:"],["facial expression:","statements:"],["statements:","gesture:"],["gesture:","emotion:"],["gesture:","--<Done>--"]]
    content_list = []
    request = None
    
    while True:
        voice_params = voicevox_config.parameters[0]
        request = requests.get(f"{config.GPT_Mangaer_URL}/LLM/get-chunk/?reset_all=false&del_request_id={request_id}").json()
        if request == []:
            await asyncio.sleep(0.2)
            continue

        for item in request:
            content += item['content']
            console.print(item['content'],style='blue',end='')
            if item['finish']==True:
                content += "\n--<Done>--"
                if item["finish_reason"] != "stop":
                    warning_message(f"GPT Request Finish Reason is Not [Stop].\nfinish_reason:{item['finish_reason']}")
                done = True
        
        # レスポンス結果より必要なデータを抜き出し
        for start_marker, end_marker in markers:
            if start_marker in content and end_marker in content:
                # 開始と終了のインデックスを見つける
                start_index = content.find(start_marker) + len(start_marker)
                end_index = content.find(end_marker)
                item = content[start_index:end_index].strip()
                if item == '':
                    continue

                if start_marker == "emotion:":
                    emotion_list = ['anger', 'disgust', 'fear', 'happy', 'sad', 'surprise','neutral']
                    emotion_text = item.lower()
                    for emotion_name in emotion_list:
                        if emotion_name in emotion_text:

                            if config.talker == 'voicevox':
                                for param in voicevox_config.parameters:
                                    if param['name'] == emotion_name:
                                        #VoiceVoxプリセット切り替え
                                        voice_params = param
                    await asyncio.sleep(0)
                
                if start_marker == "facial expression:":
                    expression_list = ['neutral', 'joy', 'angry', 'fun']
                    expression_text = item.lower()
                    for expression_name in expression_list:
                        if expression_name in expression_text:
                            #表情の更新
                            console.print("<Unity> 表情変更: ",style='green',end='')
                            print(expression_name)
                            requests.post(url=f"{config.AI_Tuber_URL}/Unity/animation/post/",json={"VRM_expression": expression_name})
                    await asyncio.sleep(0)

                if start_marker == 'gesture:':
                    #ジェスチャー類似検索実施
                    gesture_dict ={}
                    anim_list = ""
                    gesture_similar_dict = requests.get(f"{config.AI_Tuber_URL}/motion_similar/get/?str_dialogue={item}&top_n={config.motion_list_top_n}")
                    gesture_similar_dict = gesture_similar_dict.json()

                    for gesture in gesture_similar_dict:
                        if 'name' in gesture and 'text' in gesture:
                            gesture_dict[gesture['name']]=gesture['text']

                    #類似モーションがあるとき
                    if len(gesture_dict) != 0:
                        for key,value in gesture_dict.items():
                            anim_list+=f"{key} : {value}\n"
                        #モーション選択をリクエスト
                        request_data = {"motion_str":item,"anim_list":anim_list}
                        requests.post(url=f"{config.AI_Tuber_URL}/LLM/request/post/?prompt_name=Statement_to_animMotion_2&stream=false",json=request_data)
                    await asyncio.sleep(0)
                            
                if start_marker == "statements:":

                    voicevox_post_data = {
                        "chara_name": "アイリ",
                        "text": item,
                        "subs": True,
                        "lipsync": True,
                        "speaker_uuid": voicevox_config.speaker_uuid,
                        "style_id": voicevox_config.style_id,
                        "speedScale": voice_params['Speaking_Speed'],
                        "pitchScale": voice_params['Voice_Pitch'],
                        "intonationScale": voice_params['Voice_Intonation'],
                        "volumeScale": voice_params['volumeScale'],
                        "prePhonemeLength": 0.1,
                        "postPhonemeLength": 0.1
                        }
                    #読み上げリクエスト
                    requests.post(f"{config.AI_Tuber_URL}/text_to_vice/voicevox/post",json=voicevox_post_data)

                    #会話ログへの追加
                    requests.post(url=f"{config.AI_Tuber_URL}/talk_log/post",json=[{"アイリ":item}])
                    await asyncio.sleep(0)

                content_list.append({start_marker:item})
                #表示した内容を受信したデータから消去する
                content = content[end_index:]
                console.print(f"{start_marker.upper()}",style="green",end='')
                print(item)
                await asyncio.sleep(0.2)
        
        if done:
            break
        if time.time() - process_airi_v17_start_time > LLM.loop_break_time:
            print(request)
            error('Task Timeout.',f'{LLM.loop_break_time}秒経過したため、タスクは強制終了されました。',{'GPT_Raw_data':request,'Result':content_list})
            break
        await asyncio.sleep(0.2)
    console.print("\n------------------アイリ v17 Result------------------",style='blue')
    for dict_data in content_list:
        for key,value in dict_data.items():
            console.print(f"{key}",style='green',end='')
            print(value)
    console.print("------------------END------------------\n",style='blue')

    process_airi_v17_start_time = time.time()
    #Check Tokens
    while True:
        #Stream後のLLM結果を受信
        request = requests.get(f"{config.GPT_Mangaer_URL}/LLM/get/?reset=false&del_request_id={request_id}").json()
        if time.time() - process_airi_v17_start_time > LLM.loop_break_time:
            print(request)
            error('Task Timeout.',f'{LLM.loop_break_time}秒経過したため、タスクは強制終了されました。 Stream後の結果を受信できませんでした。',{'GPT_Raw_data':request,'Result':content_list})
            break
        if len(request)==0:
            await asyncio.sleep(1)
            continue
        else:
            model_name = request[0]['model']
            if 'gpt' in model_name:
                if request[0]['total_tokens'] < LLM.total_token_summary_trigger[model_name]:
                    break
            elif 'gemini' in model_name:
                if request[0]['completion_tokens'] < LLM.completion_token_summary_trigger[model_name]:
                    break

            process_dict = requests.get(f"{config.AI_Tuber_URL}/summary_process/get/").json()
            if process_dict['summary_talk'] == True and process_dict['summary_game'] == True :
                #要約中の場合
                console.print(f"--- <要約中のため要約をパスしました> ----",style='yellow')
                break

            #要約フラグ作成
            console.print("--- <ログを要約します> ----",style='yellow')
            requests.post(f"{config.AI_Tuber_URL}/summary_process/post/?summary_process=true") # 要約process True
            requests.post(f"{config.AI_Tuber_URL}/LLM/request/post/?prompt_name=talk_logTosummary&stream=false")
            #ゲームプレイ中は、ゲームログ要約も実施
            if requests.get(f"{config.AI_Tuber_URL}/GameName/get").json()!= "":
                requests.post(f"{config.AI_Tuber_URL}/summary_process/post/?summray_game_process=true")
                requests.post(f"{config.AI_Tuber_URL}/LLM/request/post/?prompt_name=game_logTosummary&stream=false")
            break
    await asyncio.sleep(1)

async def Statement_to_animMotion(request_id):
    request = requests.get(f"{config.GPT_Mangaer_URL}/LLM/get/?reset_all=false&del_request_id={request_id}").json()
    try:
        gesture_str = request[0]['content']
    except Exception as e:
        gesture_str = "None"
        error("Error Statement_to_animMotion",e,{'request':request,'request_id':request_id})
    if gesture_str != "None":
        requests.post(url=f"{config.AI_Tuber_URL}/Unity/animation/post/",json={"VRM_animation": gesture_str})
        console.print("<Unity> モーションを変更:",style='green',end='')
        print(gesture_str)
    await asyncio.sleep(1)

async def process_talk_logTosummary(request_id):
    #要約が受信された場合
    for i in range(3):
        request = requests.get(f"{config.GPT_Mangaer_URL}/LLM/get/?reset_all=false&del_request_id={request_id}").json()
        if request != []:
            break
        await asyncio.sleep(1)
    summary = request[0]['content']
    console.print("--- <会話ログを要約しました> ----",style='yellow')
    print(summary)
    requests.post(f"{config.AI_Tuber_URL}/summary/post",json={"summary":summary})
    requests.post(f"{config.AI_Tuber_URL}/summary_process/post/?summary_process=false")
    #要約したデータの消去
    talk_log = requests.get(f"{config.AI_Tuber_URL}/talk_log/get?reset=true").json()
    old_talk_log = summary_data.chara_talk_log
    filtered_talk_logs = [item for item in talk_log if item not in old_talk_log]
    requests.post(url=f"{config.AI_Tuber_URL}/talk_log/post",json=filtered_talk_logs)
    await asyncio.sleep(1)

async def process_game_logTosummary(request_id):
    #ゲームログの要約が受信した場合
    for i in range(3):
        request = requests.get(f"{config.GPT_Mangaer_URL}/LLM/get/?reset_all=false&del_request_id={request_id}").json()
        if request != []:
            break
        await asyncio.sleep(1)
    summary = request[0]['content']
    console.print("--- <ゲーム要約を要約しました> ----",style='yellow')
    print(summary)
    requests.post(f"{config.AI_Tuber_URL}/GameData/summary/post",json={"summary":summary})
    requests.post(f"{config.AI_Tuber_URL}/summary_process/post/?summray_game_process=false")
    #要約したデータの消去
    talk_log = requests.get(f"{config.AI_Tuber_URL}/GameData/talk_log/get?reset=true").json()
    old_talk_log = summary_data.game_talk_log
    filtered_talk_logs = [item for item in talk_log if item not in old_talk_log]
    requests.post(url=f"{config.AI_Tuber_URL}/GameData/talk_log/post",json=filtered_talk_logs)
    await asyncio.sleep(1)