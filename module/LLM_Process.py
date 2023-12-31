import requests,asyncio
from module.voicevox import *
from rich.console import Console

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
    total_token_summary_trigger = {"gpt-4-1106-preview":3171,"gpt-4":6143}
    completion_token_summary_trigger = {"gemini-pro":6144}

class voicevox:
    # 一時的、VoiceVox移行後消去
    voicevox_name = 'AIRI'
    speaker_uuid = "9f3ee141-26ad-437e-97bd-d22298d02ad2"
    style_id = 20
    parameters = [{'name':'neutral','Speaking_Speed':1,'Voice_Pitch':0,'Voice_Intonation':1},
                 {'name':'anger','Speaking_Speed':1,'Voice_Pitch':-0.05,'Voice_Intonation':0.8},
                 {'name':'disgust','Speaking_Speed':1,'Voice_Pitch':-0.1,'Voice_Intonation':0.6},
                 {'name':'fear','Speaking_Speed':1.2,'Voice_Pitch':0.08,'Voice_Intonation':1.2},
                 {'name':'happy','Speaking_Speed':1,'Voice_Pitch':0.05,'Voice_Intonation':1.5},
                 {'name':'sad','Speaking_Speed':0.9,'Voice_Pitch':0.09,'Voice_Intonation':1.3},
                 {'name':'surprise','Speaking_Speed':1,'Voice_Pitch':0.05,'Voice_Intonation':1.1}]

async def process_airi_v17(request_id):
    """
    アイリ v17向け処理関数
    Streamのみ対応
    """
    content = ""
    done = False
    #切り取りマーカーリスト
    markers = [["# Organize Your Thoughts:","#Result:"],["# Organize Your Thoughts:","# Result:"],["emotion:","facial expression:"],["facial expression:","statements:"],["statements:","gesture:"],["gesture:","emotion:"],["gesture:","--<Done>--"]]
    content_list = []
    
    while True:
        request = requests.get(f"{config.GPT_Mangaer_URL}/LLM/get-chunk/?reset_all=false&del_request_id={request_id}").json()
        #request = await get_data_from_server(URL=f"{config.GPT_Mangaer_URL}/LLM/get-chunk/?reset_all=false&del_request_id={request_id}")
        for item in request:
            content += item['content']
            if item['finish_reason']=="Done":
                content += "\n--<Done>--"
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
                                for param in voicevox.parameters:
                                    if param['name'] == emotion_name:
                                        #VoiceVoxプリセット切り替え
                                        update_preset(1,voicevox.voicevox_name,voicevox.speaker_uuid,voicevox.style_id,param['Speaking_Speed'],param['Voice_Pitch'],param['Voice_Intonation'])
                
                if start_marker == "facial expression:":
                    expression_list = ['neutral', 'joy', 'angry', 'fun']
                    expression_text = item.lower()
                    for expression_name in expression_list:
                        if expression_name in expression_text:
                            #表情の更新
                            console.print("表情変更: ",style='blue',end='')
                            print(expression_name)
                            requests.post(url=f"{config.AI_Tuber_URL}/Unity/animation/post/",json={"VRM_expression": expression_name})

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
                            

                if start_marker == "statements:":
                    #読み上げ実施
                    console.print("読み上げ実施:",style='blue',end='')
                    print(item)
                    stream = audio_stream_start()
                    audio_data = text_to_wave(item,preset_id=1,speaker=voicevox.style_id)
                    stream.write(audio_data)
                    audio_stream_stop(stream)

                    #会話ログへの追加
                    requests.post(url=f"{config.AI_Tuber_URL}/talk_log/post",json={"アイリ":item})

                content_list.append({start_marker:item})
                #表示した内容を受信したデータから消去する
                content = content[end_index:]
                console.print(f"{start_marker.upper()}",style="green",end='')
                print(item)
        
        if done:
            break
        await asyncio.sleep(0.2)
    for dict_data in content_list:
        for key,value in dict_data.items():
            console.print(f"{key}",style='green',end='')
            print(value)

    #Check Tokens
    while True:
        request = requests.get(f"{config.GPT_Mangaer_URL}/LLM/get/?reset=false&del_request_id={request_id}").json()
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
            #要約フラグ作成
            print("ログを要約します")
            requests.post(f"{config.AI_Tuber_URL}/LLM/request/post/?prompt_name=talk_logTosummary&stream=false")
            #ゲームプレイ中は、ゲームログ要約も実施
            if requests.get(f"{config.AI_Tuber_URL}/GameName/get")!= "":
                requests.post(f"{config.AI_Tuber_URL}/LLM/request/post/?prompt_name=game_logTosummary&stream=false")

    await asyncio.sleep(1)

async def Statement_to_animMotion(request_id):
    request = requests.get(f"{config.GPT_Mangaer_URL}/LLM/get/?reset_all=false&del_request_id={request_id}").json()
    gesture_str = request[0]['content']
    if gesture_str != "None":
        requests.post(url=f"{config.AI_Tuber_URL}/Unity/animation/post/",json={"VRM_animation": gesture_str})
        console.print("モーションを変更",style='green',end='')
        print(gesture_str)

async def process_talk_logTosummary(request_id):
    #要約が受信された場合
    print("要約を変更しました")
    request = requests.get(f"{config.GPT_Mangaer_URL}/LLM/get/?reset_all=false&del_request_id={request_id}").json()
    summary = request[0]['content']
    requests.post(f"{config.GPT_Mangaer_URL}/summary/post?summary={summary}")
    await asyncio.sleep(1)

async def process_game_logTosummary(request_id):
    #ゲームログの要約が受信した場合
    print("ゲーム要約を変更しました")
    request = requests.get(f"{config.GPT_Mangaer_URL}/LLM/get/?reset_all=false&del_request_id={request_id}").json()
    summary = request[0]['content']
    requests.post(f"{config.GPT_Mangaer_URL}/GameData/summary/post?summary={summary}")
    await asyncio.sleep(1)