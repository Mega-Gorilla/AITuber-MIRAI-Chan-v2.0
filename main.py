
from module.rich_desgin import error,warning_message
from module.server_requests import *
from module.fast_whisper import *
from rich import print
from rich.table import Table
from rich.console import Console
from collections import deque
import multiprocessing
import time
import os
import asyncio
from httpx import ConnectError, HTTPStatusError

class config:
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
    talk_logs = ""
    stream_summary = ""
    viewer_count = 0
    subscriber_count = 0
    stream = True

console = Console()

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
    while requests.get(f"{config.AI_Tuber_URL}/Program_Fin_bool/get/").text.lower() == 'false':
        response = requests.get(f"{config.AI_Tuber_URL}/mic_mute/get/")
        if response.text.lower() == 'false':
            
            try:
                speech_to_text.process_stream()
            finally:
                print('mic end.')
                # 終了時にバッファをファイルに保存
                speech_to_text.save_buffer_to_file('output.wav')
                speech_to_text.transcribe('output.wav')
                speech_to_text.close()
                requests.post(f"{config.AI_Tuber_URL}/AI_talk_bool/post/?AI_talk=true")
        else:
            time.sleep(1)

async def Mirai_15_model():
    # 会話検索エンジンの初期化
    await get_data_from_server(f"{config.AI_Tuber_URL}/similar_dialogue/start/")

    # YoutubeAPIが設定されているか確認
    commnet_url = await get_data_from_server(f"{config.AI_Tuber_URL}/youtube_api/get_stream_url/")
    if commnet_url == "":
        warning_message("Stream URLが設定されていません。Youtube APIが利用できません!")
    else:
        await youtube_counter_initialize()
    
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
                if config.viewer_count == new_viewer_count:
                    viewer_count = f"{new_viewer_count} (Viewership Change: 0)"
                else:
                    viewer_count = f"{new_viewer_count} (Viewership Change: {new_viewer_count-config.viewer_count})"
                config.viewer_count = new_viewer_count

            subscriber_count = "No Data."
            if new_subscriber_count['ok']==True:
                if config.subscriber_count == new_subscriber_count:
                    subscriber_count = f"{new_subscriber_count} (Viewership Change: 0)"
                else:
                    subscriber_count = f"{new_subscriber_count} (Viewership Change: {new_subscriber_count-config.subscriber_count})"
                config.subscriber_count = new_subscriber_count
            
            #マイク音声を取得
            mic_recorded_str = await get_mic_recorded_str()

            #類似会話例を取得
            streamer_tone_dict = await get_data_from_server(f"{config.AI_Tuber_URL}/similar_dialogue/get/?str_dialogue={mic_recorded_str}&top_n={config.tone_example_top_n}")
            streamer_tone = ''
            
            for d in streamer_tone_dict:
                if 'ok' in d:
                    if d['ok']==False:
                        streamer_tone = 'None'
                elif 'text' in d:
                    streamer_tone+=d['text']+"\n"

            mirai_prompt_variables={"Avator_Name":config.Avator_Name,
                                    "collaborator_name":config.collaborator_name,
                                    "example_tone":streamer_tone,
                                    "stream_summary":config.stream_summary,
                                    "talk_logs":config.talk_logs,
                                    "subscribers_num":subscriber_count,
                                    "viewers_num":viewer_count,
                                    "viewer_comments":new_comment_str}
            stream_mode = config.stream
            for item in mirai_prompt_variables:
                print(item)
            #リクエスト追加
            #await post_data_from_server(URL=f"{config.GPT_Mangaer_URL}/openai/request/?prompt_name={mirai_prompt_name}&stream_mode={stream_mode}",post_data={"variables" : mirai_prompt_variables})
        else:
            #GPTのデータを受信
            requests = await get_data_from_server(URL=f"{config.GPT_Mangaer_URL}/openai/get/?reset=true")
            if requests != []:
                for request_data in requests:
                    print(request_data)
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