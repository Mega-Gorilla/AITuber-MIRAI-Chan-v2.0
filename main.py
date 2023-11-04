
from module.whisper_speech_to_text import speech_to_text as whisper
from module.rich_desgin import error,warning_message
from module.server_requests import *
from rich import print
from rich.table import Table
from rich.console import Console
from collections import deque
from find_similar import AnswerFinder
import multiprocessing
import dill
import os
import asyncio
import httpx
from httpx import ConnectError, HTTPStatusError

class config:
    #Streamer memory
    directory = 'C:/Users/MegaGorilla/Documents/AI/AI_tuber_Train_Data/音声→文字データ/2.字幕_クリーニング済み'
    streamer_vector_path = 'data/streamer_vector.pkl'
    #URL
    GPT_Mangaer_URL = "http://127.0.0.1:8000"
    AI_Tuber_URL = "http://127.0.0.1:8001"

    comment_num = 5
    #みらい1.5 プロンプト
    Avator_Name = "未来 アイリ"
    collaborator_name = "猩々 博士"
    talk_logs = ""

console = Console()

def display_table(data_history, columns):
    """
    データの履歴とカラム名を受け取り、それをrichのテーブルとして表示する関数

    Parameters:
    - data_history (list): テーブルに表示するデータのリスト
    - columns (list): テーブルのカラム名のリスト

    Example:
    display_table([(1, 'John', 'Doe'), (2, 'Jane', 'Smith')], ['ID', 'First Name', 'Last Name'])
    """

    # richのTableクラスをインスタンス化。このテーブルはヘッダーと線を表示する。
    table = Table(show_header=True, header_style="bold magenta",show_lines=True)
    
    # カラムをテーブルに動的に追加
    for col_name in columns:
        table.add_column(col_name)  # 与えられたカラム名をテーブルに追加する。

    # 履歴のデータをテーブルに追加
    for row_data in data_history:
        # データを文字列に変換してテーブルの行として追加する。
        # 例: (1, 'John', 'Doe') -> "1", "John", "Doe"
        table.add_row(*map(str, row_data))

    # コンソールの現在の内容をクリア
    console.clear()
    
    # テーブルをコンソールに表示する
    console.print(table)

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
    commnet_url = await get_data_from_server(f"{config.AI_Tuber_URL}/youtube_api/get_stream_url/")
    viewer_count=''
    if commnet_url == "":
        viewer_count = "No Data."
    viewer_count = await get_data_from_server(f"{config.AI_Tuber_URL}/youtube_api/viewer_count/")
    if viewer_count['ok']:
        viewer_count = viewer_count['viewer_count']
    else:
        viewer_count = "No Data."
    return viewer_count

async def get_mic_recorded_str():
    mic_recorded_list = await get_data_from_server(f"{config.AI_Tuber_URL}/mic_recorded_list/get/?reset=true")
    if mic_recorded_list == []:
        result = ""
    else:
        result = '\n'.join(sublist[0] for sublist in mic_recorded_list)
    return result

# 処理結果に基づいて次のタスクを決定する
async def handle_results(result_queue,task_queue):
    chatLog=''
    chatLog_lineMax=3
    summary=''
    mirai_example=''
    summarize = False

    table_history = deque(maxlen=3)
    column_names = ["Job Status", "Short Memory", "Long Memory", "Ex. Memory"]

    #Streamer Example
    print("ベクトルを作成中....")
    finder = AnswerFinder(config.directory,config.streamer_vector_path)
    print("ベクトル作成完了")

    while True:
        job_status=''

        #結果を取得する
        result = await result_queue.get()
        result_ID = result["ID"]
        result_message = result["message"]
        
        #グローバル関数更新
        global_dict = await get_data_from_server()
        if "talkFlag" in global_dict:
            talkFlag = global_dict["talkFlag"]
        if "speechToText" in global_dict:
            speechToText = global_dict["speechToText"]
        
        # User会話データがあった時、
        if result_ID == 'speech':
            #User 会話履歴の追加
            userTalkStr = result_message
            chatLog += (f"{UserName}:{userTalkStr}\n")

            job_status+='ユーザー会話追加\n'

            if talkFlag: #Talkボタンが押された時
                talkFlag = False

                #メモリより類似会話の検索
                streamer_ex = finder.find_similar(userTalkStr)
                mirai_example = '\n'.join([item[0] for item in streamer_ex])

                miraichan_talk_task = request_GPT(ID="talkStr",
                                                  prompt_name='miraiV2',
                                                  user_prompt=[],
                                                  variables={
                                                      "chatLog":chatLog,
                                                        "summary":summary,
                                                        "mirai_example":mirai_example},
                                                    stream=True)
                #グローバル配列情報の更新
                global_dict = await get_data_from_server()
                global_dict["talkFlag"] = False
                await post_data(global_dict)

                job_status+='みらい会話問い合わせ実施\n'
                #Jobを追加
                await task_queue.put(miraichan_talk_task)

        # Mirai Chan Talk が出力された時、
        if result_ID == 'talkStr':
            if ":" in result_message:  # コロンが存在するか確認
                index_of_colon = result_message.index(":")
                # コロンの前の部分が20文字以下である場合、コロンを含めて削除
                if index_of_colon <= 20:
                    result_message = result_message[index_of_colon+1:]

            result_message = result_message.replace("\n", "")
            result_message = result_message.replace('"', "")
            #みらい　会話履歴の追加
            chatLog+=(f"Mirai Chan:{result_message}")

            job_status+='みらい会話発話実施\n'

        # 要約が出力されたとき、
        if result_ID == 'summaryStr':
            #print(f"要約の実施\n{chatLog}->{result_message}")
            #要約変数に要約結果を追加
            summary = result_message
            #ショートメモリから要約した内容を消去
            chatlog_lines = chatLog.split("\n")
            chatLog = "\n".join(chatlog_lines[chatLog_lineMax:])
            summarize = False

            job_status+='要約適応実施'

        # ショートメモリ(chatlog)が一定行数以上になった時要約を依頼
        if chatLog.count('\n')+1 > chatLog_lineMax and summarize == False:
            #ショートメモリが一定数以上になった時要約する
            summary_task = request_GPT(ID='summaryStr',
                                       prompt_name='talkSummary',
                                       user_prompt=[],
                                       variables={
                                                "charactor_profile":chara_profile, 
                                                "summary":summary,
                                                "chat_log":chatLog},
                                        stream=True)
            summarize = True
            job_status+= '要約作成実施'
            await task_queue.put(summary_task)
        
        #UIを更新
        table_history.append([job_status,chatLog,summary,mirai_example])  # 最新のデータを履歴に追加
        display_table(table_history, column_names)  # テーブルを表示
        mirai_example=""

        await asyncio.sleep(0.5)

#Process1 にて実行
async def record_to_text(model):
    recording_swicth = await get_data_from_server(f"{config.AI_Tuber_URL}/mic_recording_bool/get/")
    if recording_swicth != True:
        return
    #Whisper 必要関数の作成
    audio_queue = asyncio.Queue()

    #asyncのタスクを保存する配列
    result_queue = asyncio.Queue()

    async_tasks = {}
    async_running_tasks = {}
    mic_recorder_task, audio_to_text_task = whisper().mic_to_text_retun_task(audio_queue, result_queue, model)
    
    #MainLoop
    while True:
        if recording_swicth != True:
            await asyncio.sleep(1)

        #タスクを追加する
            #声認識タスクを追加
        if "mic_recorder_task" not in async_running_tasks and recording_swicth:
            async_tasks["mic_recorder_task"] = lambda: mic_recorder_task
            async_tasks["audio_to_text_task"] = lambda: audio_to_text_task
        
        #taskキューを実行する
        if len(async_tasks) != 0:
            for name, task_func in list(async_tasks.items()):
                task = asyncio.create_task(task_func())  # Call the lambda to get a new coroutine object.
                async_running_tasks[name] = task
                del async_tasks[name] # Remove the task from the dictionary
        #result_queueより
        while result_queue.qsize()!=0:
            result_data = await result_queue.get()
            for key, value in result_data.items():
                if key == 'whisper_text':
                    await post_data_from_server(post_data=[value],URL=f"{config.AI_Tuber_URL}/mic_recorded_list/post/")
            #print(f"結果: {result_data}")
            
        #関数を更新
        recording_swicth = await get_data_from_server(f"{config.AI_Tuber_URL}/mic_recording_bool/get/")
        whisper().change_recording_state(recording_swicth)
        await asyncio.sleep(0)

def process1_function():
    #Whisper modelの準備
    print("Create Whisper Model...",end='')
    model = whisper().create_whisper_model()
    print("Done.")
    asyncio.run(record_to_text(model))

async def Mirai_15_model():
    commnet_url = await get_data_from_server(f"{config.AI_Tuber_URL}/youtube_api/get_stream_url/")
    if commnet_url == "":
        warning_message("Stream URLが設定されていません。配信コメントは取得されません。")
    while True:
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
            viewer_count = await get_youtube_viewer_counts()

            #マイク音声を取得
            mic_recorded_list = await get_mic_recorded_str()
            print(f"mic_data:{mic_recorded_list}\nviewers:{viewer_count}\ncomments:{new_comment_str}")
        else:
            await asyncio.sleep(1)

def process2_function():
    asyncio.run(Mirai_15_model())

if __name__ == "__main__":

    #multiprocessing用プロセス作成
    process1 = multiprocessing.Process(target=process1_function)
    process2 = multiprocessing.Process(target=process2_function)

    #multiprocessingプロセス開始
    process1.start()
    process2.start()

    process1.join()
    process2.join()