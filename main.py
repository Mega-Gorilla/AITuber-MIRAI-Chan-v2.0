
from module.rich_desgin import error,warning_message
from module.server_requests import *
from module.fast_whisper import *
from rich import print
from rich.console import Console
import multiprocessing
import time
import asyncio
import os
import json
import aiohttp

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

    comment_num = 5
    tone_example_top_n = 4

    #みらい1.5 プロンプト
    Avator_Name = "未来 アイリ"
    collaborator_name = "猩々 博士"
    talk_logs = []
    stream_summary = ""
    viewer_count = 0
    subscriber_count = 0
    stream = False
    requestList = {}

    summary_limit_token = 4000 #このトークン値を超えたら要約されます。
    total_token = 0

console = Console()

async def translate_text(text, target_language,source_language='EN'):
    
    endpoint = 'https://api-free.deepl.com/v2/translate'

    # 翻訳リクエストのパラメータ
    params = {
        'auth_key': config.Deepl_API_key,
        'text': text,
        'target_lang': target_language,
        'source_lang': source_language
    }

    # aiohttp.ClientSessionを使用してリクエストを非同期で実行
    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, data=params) as response:
            # レスポンスをJSONとして解析
            result = await response.json()
            return result['translations'][0]['text']
        
async def youtube_counter_initialize():
    viewer_count = await get_youtube_viewer_counts()
    if "viewer_count" in viewer_count:
        config.viewer_count = viewer_count['viewer_count']
    subscriber_count = await get_youtube_subscriber_counts()
    if "subscriber_count" in subscriber_count:
        config.subscriber_count = subscriber_count['subscriber_count']

async def get_youtube_comments_str():
    #Youtubeデータ取得
    new_comment_str = ""
    if await get_data_from_server(f"{config.AI_Tuber_URL}/youtube_api/chat_fetch/sw-get/"):
        new_comment_dict = await get_data_from_server(f"{config.AI_Tuber_URL}/youtube_api/chat_fetch/get/?reset=true")
        if new_comment_dict!=[]:
            comment_len=len(new_comment_dict)
            if config.comment_num < comment_len:
                comment_len = config.comment_num
            for i in range(comment_len):
                if new_comment_dict[i]['superchat_bool']:
                    new_comment_str += f"({new_comment_dict[i]['name']}:{new_comment_dict[i]['comment']} [Important Information: Received {new_comment_dict[i]['superchat_currency']}{new_comment_dict[i]['superchat_value']} super chat!!])"
                new_comment_str += f"({new_comment_dict[i]['name']}:{new_comment_dict[i]['comment']})"
        else:
            new_comment_str = "None."
    return new_comment_str

async def get_youtube_viewer_counts():
    viewer_count = await get_data_from_server(f"{config.AI_Tuber_URL}/youtube_api/viewer_count/")
    return viewer_count

async def get_youtube_subscriber_counts():
    subscriber_counts = await get_data_from_server(f"{config.AI_Tuber_URL}/youtube_api/subscriber_count/")
    return subscriber_counts

async def get_mic_recorded_str():
    mic_recorded_list = await get_data_from_server(f"{config.AI_Tuber_URL}/mic_recorded_list/get/?reset=true")
    if mic_recorded_list == []:
        result = ""
    else:
        result = '\n'.join([''.join(item) for item in mic_recorded_list])
    return result

def process1_function():
    #マイク音声聞き取り＋文字化
    speech_to_text = AudioProcessor()
    audio_repeat = False
    try:
        while requests.get(f"{config.AI_Tuber_URL}/Program_Fin_bool/get/").text.lower() == 'false':
            response = requests.get(f"{config.AI_Tuber_URL}/mic_mute/get/")
            if response.text.lower() == 'false':           
                speech_to_text.process_stream()
                print('mic end.')
                speech_to_text.stop()
                # 終了時にバッファをファイルに保存
                speech_to_text.save_buffer_to_file('output.wav')
                speech_to_text.reset()
                speech_to_text.start()

                speech_to_text.transcribe('output.wav')
                audio_repeat = True
                requests.post(f"{config.AI_Tuber_URL}/AI_talk_bool/post/?AI_talk=true")
            else:
                if audio_repeat:
                    speech_to_text.play_wav_file('output.wav')
                    audio_repeat = False
                time.sleep(1)
    except Exception as e:
        # ここでエラーを処理する
        print(f"予期せぬエラーが発生しました: {e}")
    finally:
        speech_to_text.close()

async def Mirai_15_model():
    # 会話検索エンジンの初期化
    await get_data_from_server(f"{config.AI_Tuber_URL}/similar_dialogue/start/")
    await get_data_from_server(URL=f"{config.GPT_Mangaer_URL}/openai/get/?reset=true")

    # YoutubeAPIが設定されているか確認
    commnet_url = await get_data_from_server(f"{config.AI_Tuber_URL}/youtube_api/get_stream_url/")
    if commnet_url == "":
        warning_message("Stream URLが設定されていません。Youtube APIが利用できません!")
    else:
        await youtube_counter_initialize()
        # コメント取得開始
        await post_data_from_server(f"{config.AI_Tuber_URL}/youtube_api/chat_fetch/sw/?chat_fecth_sw=true")
    
    while await get_data_from_server(f"{config.AI_Tuber_URL}/Program_Fin_bool/get/") == False:
        mirai_prompt_name = 'みらいV1.5'
        mirai_talkSW = await get_data_from_server(f"{config.AI_Tuber_URL}/AI_talk_bool/get/") 

        if mirai_talkSW:
            #会話ボタンを押した場合の処理
            await post_data_from_server(URL=f"{config.AI_Tuber_URL}/AI_talk_bool/post/",post_data={'AI_talk': False}) #問合せフラグをFalseに
            
            #みらいプロンプトに必要な関数情報を取得
            mirai_prompt_data = await get_data_from_server(f"{config.GPT_Mangaer_URL}/prompts-get/lookup_prompt_by_name?prompt_name={mirai_prompt_name}")
            mirai_prompt_variables = mirai_prompt_data['variables']
            
            #Youtubeデータ取得
            new_comment_str = await get_youtube_comments_str()
            new_viewer_count = await get_youtube_viewer_counts()
            new_subscriber_count = await get_youtube_subscriber_counts()

            viewer_count = "No Data."
            if new_viewer_count['ok']==True:
                if config.viewer_count == new_viewer_count['viewer_count']:
                    viewer_count = f"{new_viewer_count['viewer_count']} (Viewership Change: 0)"
                else:
                    viewer_count = f"{new_viewer_count['viewer_count']} (Viewership Change: {new_viewer_count['viewer_count']-config.viewer_count})"
                config.viewer_count = new_viewer_count['viewer_count']

            subscriber_count = "No Data."
            if new_subscriber_count['ok']==True:
                if config.subscriber_count == new_subscriber_count['subscriber_count']:
                    subscriber_count = f"{new_subscriber_count['subscriber_count']} (Subscriber Change: 0)"
                else:
                    subscriber_count = f"{new_subscriber_count['subscriber_count']} (Subscriber Change: {new_subscriber_count['subscriber_count']-config.subscriber_count})"
                config.subscriber_count = new_subscriber_count['subscriber_count']
            
            #マイク音声を取得
            mic_recorded_str = await get_mic_recorded_str()
            config.talk_logs.append({"猩々 博士":mic_recorded_str})

            #類似会話例を取得
            serch_tone_word = mic_recorded_str.split('\n')[0]
            streamer_tone_dict = await get_data_from_server(f"{config.AI_Tuber_URL}/similar_dialogue/get/?str_dialogue={serch_tone_word}&top_n={config.tone_example_top_n}")
            streamer_tone = ''
            for d in streamer_tone_dict:
                if 'ok' in d:
                    if d['ok']==False:
                        streamer_tone = 'None'
                elif 'text' in d:
                    streamer_tone+=d['text']+"\n"

            #会話ログを作成
            talk_log = ""
            if config.talk_logs != []:
                for d in config.talk_logs:
                    key, value = list(d.items())[0]
                    talk_log += f"{key} -> {value}\n"
                talk_log = talk_log.rstrip('\n')

            mirai_prompt_variables = {
                "Avator_Name": config.Avator_Name,
                "collaborator_name": config.collaborator_name,
                "example_tone": streamer_tone,
                "stream_summary": config.stream_summary,
                "talk_logs": talk_log,
                "subscribers_num": subscriber_count,
                "viewers_num": viewer_count,
                "viewer_comments": new_comment_str
            }
            stream_mode = config.stream
            print("\n------------------Prompt Data------------------")
            for key,value in mirai_prompt_variables.items():
                print(f"{key}: {value}")
            print("------------------ END ------------------")

            #リクエスト追加
            config.requestList = {mirai_prompt_name:{"variables" : mirai_prompt_variables}}
            await post_data_from_server(URL=f"{config.GPT_Mangaer_URL}/openai/request/?prompt_name={mirai_prompt_name}&stream_mode={stream_mode}",post_data={"variables" : mirai_prompt_variables})
        else:
            #GPTのデータを受信
            requests = await get_data_from_server(URL=f"{config.GPT_Mangaer_URL}/openai/get/?reset=true")
            message_list = []
            translate_dir = {}
            emotion_statements_list = []
            usage_data={}
            # GPTレスポンスデータを取得する
            if requests != []:
                for request_data in requests:
                    try:
                        if 'choices' in request_data:
                            #データを取得し、辞書配列に変換する
                            message_list.append(json.loads(request_data["choices"][0]['message']['content']))
                            usage_data[request_data['request_id']] = request_data['usage']['total_tokens']
                            config.total_token += request_data['usage']['total_tokens']
                        else:
                            prompt_name = request_data['request_id']
                            print(f"問題のある投稿が行われました。{prompt_name}を再リクエストします")
                            print(request_data)
                            await post_data_from_server(URL=f"{config.GPT_Mangaer_URL}/openai/request/?prompt_name={prompt_name}&stream_mode=false",post_data=config.requestList[prompt_name])
                    except Exception as e:
                        print('Add JOB: [str to Json]')
                        await post_data_from_server(URL=f"{config.GPT_Mangaer_URL}/openai/request/?prompt_name=str to Json&stream_mode=false",post_data={"variables":{"str_data":request_data["choices"][0]['message']['content']}})
            
            #要約を実施する
            if usage_data!={}:
                if usage_data['みらいV1.5'] > config.summary_limit_token:
                    print("\033[31mプロンプト長さが規定値を超えました.\033[0m")
                    pass

            #結果を表示する
            if message_list != []:
                print("\n------------------Result Data------------------")
                for item in message_list:
                    #音声データが来た場合の対処
                    if 'Result' in item: 
                        emotion_statements_list = item['Result'] #会話データ＋感情データを配列で取得
                        for talk_data in item['Result']: #会話データを取得しlogに挿入する
                            #{'emotion': 'Amused and intrigued', 'statements': '会話データ'}
                            append_data = talk_data['statements']
                            print_data = f"未来 アイリ -> {append_data}"
                            print("\033[92m"+{print_data}+"\033[0m")
                            config.talk_logs.append({"未来 アイリ":append_data})
                        
                        #翻訳文を追加
                        translate_dir["コラボ相手の活動内容"] = item["Summary of Collaborator's Activities"]
                        translate_dir["視聴者からのフィードバック"] = item["Summary of Viewer Feedback Analysis"]
                        translate_dir['エンゲージメントを上昇させるためには？'] = item['Summary of Strategies for Engagement']
                    #print(f"{item}")

                #翻訳する
                if translate_dir != {}:
                    for key,value in translate_dir.items():
                        translate_str = await translate_text(value,'JA')
                        print(f"{key}: {translate_str}")
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