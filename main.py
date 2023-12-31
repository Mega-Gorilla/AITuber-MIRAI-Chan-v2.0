
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
    #keys
    Deepl_API_key = os.getenv("DEEPL_API_KEY")

    #mic
    mic_mute= True

    #Streamer memory
    directory = 'memory\example_tone'
    streamer_vector_path = 'memory\example_tone\streamer_vector.pkl'

    #URL
    GPT_Mangaer_URL = "http://127.0.0.1:8000"
    AI_Tuber_URL = "http://127.0.0.1:8001"

    #コメント参照個数
    comment_num = 4

    #類似検索個数
    tone_example_top_n = 3
    motion_list_top_n = 4

    #要約
    summary_len = 5 #要約時log要素数が、summary_len要素以下の場合、要約は行われません。
    game_summary = "None"
    game_logs_temp = []

    #みらい1.5 プロンプト
    mirai_prompt_name = 'airi_v17_gemini'
    talk_logs = []
    talk_log_temp = []
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
        "airi_v17":request_airi_v17,
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
    commnet_url = await get_data_from_server(f"{config.AI_Tuber_URL}/youtube_api/get_stream_url/")
    if commnet_url == "":
        warning_message("Stream URLが設定されていません。Youtube APIが利用できません!")
    else:
        await youtube_counter_initialize()
        # コメント取得開始
        await post_data_from_server(f"{config.AI_Tuber_URL}/youtube_api/chat_fetch/sw/?chat_fecth_sw=true")

async def get_mic_recorded_str():
    mic_recorded_list = await get_data_from_server(f"{config.AI_Tuber_URL}/mic_recorded_list/get/?reset=true")
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

    print("\n------------------Prompt Data------------------")
    for key,value in variables.items():
        print(f"{key}: {value}")
    print("------------------ END ------------------")

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
                #requests.post(url=f"{config.AI_Tuber_URL}/StoT_process/post/",json=True) 
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
    await get_data_from_server(URL=f"{config.GPT_Mangaer_URL}/LLM/get/?reset=true") #回答履歴を消去

    Add_preset(1,config.voicevox_name,config.speaker_uuid,config.style_id) #ViceVoxの初期化
    stream = audio_stream_start()
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
                LLM_results_list = await get_data_from_server(f"{config.GPT_Mangaer_URL}/LLM/get/?reset=false") #LLM結果の取得
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
            continue
            #LLMの回答データの取得
            requestss = await get_data_from_server(URL=f"{config.GPT_Mangaer_URL}/LLM/get/?reset=true")
            message_list = []
            usage_data = {}

            # GPTレスポンスデータを取得する
            if requestss != []:
                for request_data in requestss:
                    try:
                        if 'choices' in request_data:
                            #OPENAI よりデータが返された時
                            request_id = request_data['request_id']
                            print(f"OpenAIからの応答: {request_id}\n{request_data['choices'][0]}\n")

                            if request_id == "talk_logTosummary":
                                #要約が送信された場合
                                content = request_data['choices'][0]['message']['content']
                                config.summary = content
                                #会話データより要約済みデータを消去
                                filtered_talk_logs = [item for item in config.talk_logs if item not in config.talk_log_temp]
                                config.talk_logs = filtered_talk_logs
                                print(f"会話要約が実施されました。\n{content}")
                                
                            elif request_id == "game_logTosummary":
                                #ゲームログの要約が受信した場合
                                content = request_data['choices'][0]['message']['content']
                                config.game_summary = content
                                print("\n------------------Summary Game Data------------------")
                                #会話データより要約済みデータを消去
                                game_log = await get_data_from_server(URL=f"{config.AI_Tuber_URL}/GameData/talk_log/get?reset=false")
                                filtered_game_log = [item for item in game_log if item not in config.game_logs_temp]
                                await post_data_from_server(URL=f"{config.AI_Tuber_URL}/GameData/talk_log/post",post_data=filtered_game_log)
                                print(f"ゲームログが要約が実施されました。\n{content}")
                                print("\n------------------ END ------------------")

                            else:
                                #OpenAIレスポンスを辞書配列に変換する
                                dict_data = json.loads(request_data["choices"][0]['message']['content'])
                                #データにプロンプト名を追加
                                if isinstance(dict_data, dict):
                                    dict_data["request_id"] = request_data['request_id']
                                elif isinstance(dict_data, list):
                                    dict_data.insert(0,{"request_id":request_data['request_id']})
                                message_list.append(dict_data)
                                
                            #コスト追加
                            usage_data[request_data['request_id']] = request_data['usage']['total_tokens']
                            config.total_token += request_data['usage']['total_tokens']
                            print(f"Total Cost: {config.total_token}")
                        else:
                            prompt_name = request_data['request_id']
                            error("OpenAIサーバー問合せ時に問題が発生しました。",request_data['choices'][0]['message'],{"RequestID":request_data['request_id'],"request_data":request_data})
                            print(f"{prompt_name}を再リクエストします。")
                            await post_data_from_server(URL=f"{config.GPT_Mangaer_URL}/LLM/request/?prompt_name={prompt_name}&stream_mode=false",post_data=config.requestList[prompt_name])
                    except Exception as e:
                        print(f'問い合わせにエラーが発生しています。\n')
                        prompt_name = request_data['request_id']
                        error("OpenAIの応答データを辞書配列に変換できませんでした。",f"{prompt_name} の変換に失敗",{"RequestID":request_data['request_id'],"request_data":request_data})
                        await post_data_from_server(URL=f"{config.GPT_Mangaer_URL}/LLM/request/?prompt_name={prompt_name}&stream_mode=false",post_data=config.requestList[prompt_name])
            
            #要約を実施する
            if usage_data!={}:
                print(f"Usage Data: {usage_data}")
                if usage_data.get(config.mirai_prompt_name, 0) > config.summary_limit_token:
                    print("プロンプト長さが規定値を超えました!!")
                    if len(config.talk_logs)>config.summary_len:
                        print("会話ログを要約します")
                        config.talk_log_temp = config.talk_logs #一時保存
                        talk_log = ""
                        for d in config.talk_logs:
                            key, value = list(d.items())[0]
                            talk_log += f"{key} -> {value}\n"
                        talk_log = talk_log.rstrip('\n')
                        old_summary = config.summary
                        await post_data_from_server(URL=f"{config.GPT_Mangaer_URL}/LLM/request/?prompt_name=talk_logTosummary&stream_mode=false",post_data={"variables": {"talk_log":talk_log,"old_talk_log":old_summary}})
                    game_title = await get_data_from_server(URL=f"{config.AI_Tuber_URL}/GameName/get")
                    if game_title != "":
                        print("GameLogを要約します")
                        game_log = await get_data_from_server(URL=f"{config.AI_Tuber_URL}/GameData/talk_log/get?reset=false")
                        config.game_logs_temp = game_log #一ぞ保存
                        game_log_str = ""
                        for d in game_log:
                            key = d["name"]
                            value = d["text"]
                            game_log_str += f"{key} -> {value}\n"
                        game_log_str = game_log_str.rstrip('\n')
                        old_game_log = config.game_summary
                        game_info = await get_data_from_server(URL=f"{config.AI_Tuber_URL}/GameData/GameInfo/get")
                        await post_data_from_server(URL=f"{config.GPT_Mangaer_URL}/LLM/request/?prompt_name=game_logTosummary&stream_mode=false",post_data={"variables": {"game_log":game_log_str,"old_game_log":old_game_log,"game_info":game_info}})

            #LLMの結果より処理を決定する
            if message_list != []: 
                print("\n------------------Result Data------------------")
                for item in message_list:
                    #print(f"message_list: {item}")
                    if isinstance(item, dict):
                        #みらい1.6の結果が返ってきた際の処理
                        if item['request_id'] == config.mirai_prompt_name: 
                            config.AI_gesture_emotion_state_list = item['Result'] #会話データ＋感情データを配列で取得
                            
                            #翻訳文を追加
                            filtered_data = {k: v for k, v in item.items() if k not in ['Result', 'request_id']}
                            config.translatedict.update(filtered_data)
                    elif isinstance(item, list):
                        if item[0]['request_id']=="statementsToVoiceVoxparameter":
                            #VoiceVox向けパラメータがある場合、
                            config.VoiceVox_list = item
                        if item[0]['request_id']=="Statement_to_animMotion":
                            config.motion_list = item
                    else:
                        print(f'分からないデータ: {item}')
                    #print(f"{item}")

            # アイリの会話文があるとき
            if config.AI_gesture_emotion_state_list != []:
                talk_log = config.talk_logs
                statement_to_motion_prompt = ""
                statement_to_voiceTone_prompt = ""
                gesture_dict ={}
                gesture_list = []
                anim_list=""
                #talklogの作成
                talk_log = ""
                if config.talk_logs != []:
                    for d in config.talk_logs:
                        key, value = list(d.items())[0]
                        talk_log += f"{key} -> {value}\n"
                    talk_log = talk_log.rstrip('\n')

                for item in config.AI_gesture_emotion_state_list:
                    #会話データの追加
                    try:
                        statement_str = item['statements'].replace("未来 アイリ: ", "")
                        emotion_str = item['emotion']
                        gesture_str = item['gesture']
                    except Exception as e:
                        error("mirai1.6ToDictが正しく辞書配列に変換できませんでした。",item,{"mirai1.6ToDict Data":item})
                        await post_data_from_server(URL=f"{config.GPT_Mangaer_URL}/LLM/request/?prompt_name=mirai1.6ToDict&stream_mode=false",post_data=config.requestList["mirai1.6ToDict"])
                        break
                    print(f"未来 アイリ -> {statement_str}")

                    statement_to_voiceTone_prompt += f"{statement_str}[{emotion_str}]\n"
                    statement_to_motion_prompt += f"{statement_str}[{gesture_str}]"
                    gesture_list.append(gesture_str)

                    # メモリーに追加
                    config.talk_logs.append({"未来 アイリ":statement_str})
                
                #VoiceTone問合せ実施
                if statement_to_voiceTone_prompt != "":
                    config.requestList = {"statementsToVoiceVoxparameter":{"variables" : {"talk_data":statement_to_voiceTone_prompt}}}
                    await post_data_from_server(URL=f"{config.GPT_Mangaer_URL}/LLM/request/?prompt_name=statementsToVoiceVoxparameter&stream_mode=false",post_data={"variables": {"talk_data":statement_to_voiceTone_prompt}})

                    #ジェスチャー類似検索実施
                    for item in gesture_list:
                        #ジェスチャーの類似検索実施
                        gesture_similar_dict = await get_data_from_server(f"{config.AI_Tuber_URL}/motion_similar/get/?str_dialogue={item}&top_n={config.motion_list_top_n}")
                        for item in gesture_similar_dict:
                            if 'name' in item and 'text' in item:
                                gesture_dict[item['name']]=item['text']
                    #animlistの個数が不足している場合ランダムで追加する
                    if len(gesture_similar_dict) <= 10:
                        gesture_list = await get_data_from_server(f"{config.AI_Tuber_URL}/Unity/animation/list/get")
                        add_list = random.sample(gesture_list,10-len(gesture_similar_dict))
                        for anim in add_list:
                            gesture_dict.update(anim)
                    #anim_listを作成する
                    for key,value in gesture_dict.items():
                        anim_list+=f"{key} : {value}\n"
                    #Motionの問い合わせ実施
                    config.requestList = {"Statement_to_animMotion":{"variables" : {"talk_data":statement_to_motion_prompt,"anim_list":anim_list}}}
                    await post_data_from_server(URL=f"{config.GPT_Mangaer_URL}/LLM/request/?prompt_name=Statement_to_animMotion&stream_mode=false",post_data={"variables": {"talk_data":statement_to_motion_prompt,"anim_list":anim_list}})
                    
                #会話データをリセットする
                config.AI_gesture_emotion_state_list = []
            
            #データがそろった際読み上げ実施する
            if config.motion_list!= [] and config.VoiceVox_list!= []:
                print(f"motionList: {config.motion_list}\nVoiceVoxList: {config.VoiceVox_list}")
                new_list = []
                VoiceVoxList = config.VoiceVox_list
                motionList = config.motion_list

                # VoiceVoxListからテキストと声のトーンを取得し、motionListからアニメーション情報を取得して組み合わせる
                for voice_item, motion_item in zip(VoiceVoxList[1:], motionList[1:]):
                    # テキストとアニメーションキーを取得
                    text = list(voice_item.values())[0]
                    anim_key = list(motion_item.keys())[0]
                    print(f"text: {text}\nanim_key: {anim_key}")

                    # 新しい形式でデータを追加
                    new_list.append({
                        "text": text,
                        "voice_tone": voice_item['voice_tone'],
                        "Expression": voice_item['Expression'],
                        "anim": motion_item[anim_key]
                    })
                
                print(f"\nResult List: {new_list}")
                #アニメーション実施
                i = 0
                for items in new_list:
                    text = items['text']
                    voice_tone = items['voice_tone']
                    Expression = items['Expression']
                    anim = items['anim']
                    unity_post_data = {"VRM_expression": Expression,
                                       "VRM_animation": anim}
                    update_preset(1,config.voicevox_name,config.speaker_uuid,config.style_id,voice_tone['Speaking_Speed']*0.01,(voice_tone['Voice_Pitch']-100)*0.01,voice_tone['Voice_Intonation']*0.01)
                    stream = audio_stream_start()
                    #text_to_wavefile(text,file_path=f"{config.voicevox_save_path}\AI_audio_{i}.wav",preset_id=1,speaker=config.style_id)
                    audio_data = text_to_wave(text,preset_id=1,speaker=config.style_id)
                    await post_data_from_server(URL=f"{config.AI_Tuber_URL}/Unity/animation/post/",post_data=unity_post_data)
                    stream.write(audio_data)
                    audio_stream_stop(stream)
                    i += 1

                config.motion_list = []
                config.VoiceVox_list = []
            
            #翻訳する
            if config.translatedict != {}:
                print()
                for key,value in config.translatedict.items():
                    translate_str = await atranslate_text(config.Deepl_API_key,value)
                    print(f"{key}: {translate_str}")
                config.translatedict = {}
                print("------------------ END ------------------")
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