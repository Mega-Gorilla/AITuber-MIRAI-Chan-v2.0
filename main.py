
from module.whisper_speech_to_text import speech_to_text as whisper
from module.rich_desgin import error
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

#Streamer memory
directory = 'C:/Users/MegaGorilla/Documents/AI/AI_tuber_Train_Data/音声→文字データ/2.字幕_クリーニング済み'
streamer_vector_path = 'data/streamer_vector.pkl'

#URL
GPT_Mangaer_URL = "http://127.0.0.1:8000"
AI_Tuber_URL = "http://127.0.0.1:8001"

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

# 非同期関数としてデータをPOSTするための関数
async def post_data_from_server(URL,post_data,post_params=None,max_retries=3, delay=1, timeout=60.0):
    """
    非同期的にデータを指定されたURLにPOSTする関数。
    Parameters:
    - URL: データを取得するURL。
    - post_data: POSTリクエストとともに送信されるデータ。
    - post_params: POSTリクエストとともに送信されるクエリパラメータ。
    - max_retries: 最大再問合せ回数。
    - delay: 再問合せの間隔（秒）。
    - timeout: リクエストのタイムアウト秒数。
    Returns:
    - dict or None: 成功時にはレスポンスのJSONデータを返し、失敗時にはNoneを返す。
    """
    
    retries = 0

    while retries < max_retries:
        try:
            request_kwargs = {
                'url':URL
            }
            # データを適切な形式でリクエストに追加
            if isinstance(post_data, (dict, list)):  # post_dataが辞書型またはリスト型の場合
                request_kwargs["json"] = post_data
            else:  # それ以外の場合、生のデータとして扱う
                request_kwargs["data"] = post_data
            # クエリパラメータをリクエストに追加
            if post_params is not None:
                request_kwargs["params"] = post_params

            # httpxの非同期クライアントを使用して非同期的なリクエストを行う
            async with httpx.AsyncClient(timeout) as client:
                response = await client.post(**request_kwargs)
                # レスポンスのステータスコードが200（成功）の場合
                response.raise_for_status()
                # レスポンスのJSONデータを返す
                return response.json()

        except ConnectError as e:
            # 接続エラーが発生した場合は、エラーメッセージを表示して、Noneを返す
            error("Connection Error:", f"{e}", {"Mode":"Post","URL": URL,"Request Data":request_kwargs,"Request Count":retries})
            retries += 1
            await asyncio.sleep(delay)
        except HTTPStatusError as e:
            # HTTPステータスエラーが発生した場合は、エラーメッセージを表示して、Noneを返す
            error("HTTP Error:", f"{e}", {"Mode":"Post","URL": URL,"Request Data":request_kwargs,"Request Count":retries})
            retries += 1
            await asyncio.sleep(delay)
        except Exception as e:
            # 上記以外のエラーが発生した場合は、エラーメッセージを表示して、Noneを返す
            error("An error occurred:", f"{e}", {"Mode":"Post","URL": URL,"Request Data":request_kwargs,"Request Count":retries})
            retries += 1
            await asyncio.sleep(delay)
    return None

# 非同期関数としてデータをGETするための関数
async def get_data_from_server(URL, max_retries=3, delay=1):
    """
    非同期的に指定されたURLからデータを取得する関数。

    Parameters:
    - URL: データを取得するURL。
    - max_retries: 最大再問合せ回数。
    - delay: 再問合せの間隔（秒）。

    Returns:
    - dict or None: 成功時にはレスポンスのJSONデータを返し、失敗時にはNoneを返す。
    """
    retries = 0

    while retries < max_retries:
        try:
            # httpxの非同期クライアントを使用して非同期的なリクエストを行う
            async with httpx.AsyncClient() as client:
                response = await client.get(URL)
                # レスポンスのステータスコードが200（成功）の場合
                response.raise_for_status()
                # レスポンスのJSONデータを返す
                return response.json()

        except ConnectError as e:
            # 接続エラーが発生した場合は、エラーメッセージを表示して、Noneを返す
            error("Connection Error:", f"{e}", {"Mode":"Get","URL": URL,"Request Count":retries})
            retries += 1
            await asyncio.sleep(delay)
        except HTTPStatusError as e:
            # HTTPステータスエラーが発生した場合は、エラーメッセージを表示して、Noneを返す
            error("HTTP Error:", f"{e}", {"Mode":"Get","URL": URL,"Request Count":retries})
            retries += 1
            await asyncio.sleep(delay)
        except Exception as e:
            # 上記以外のエラーが発生した場合は、エラーメッセージを表示して、Noneを返す
            error("An error occurred:", f"{e}", {"Mode":"Get","URL": URL,"Request Count":retries})
            retries += 1
            await asyncio.sleep(delay)
    print(f"All {max_retries} connection attempts failed.")
    return None

# GPTにリクエストするための非同期関数
async def request_GPT(ID, prompt_name, user_assistant_prompt=None, variables=None, stream=False):
    """
    非同期的にGPTにリクエストを送る関数。

    Parameters:
    - ID (str or int): リクエストに関連する一意のID。
    - prompt_name (str): エンドポイントの一部として使用するプロンプト名。
    - user_prompt (str): GPTに送る実際のプロンプト。
    - variables (dict): GPTに送る追加の変数。
    - stream (bool): ストリーミングモードの有効/無効を指定。

    Returns:
    - dict: レスポンス情報を含む辞書。
    """
    
    # リクエストデータの構築
    request_data = {}
    if user_assistant_prompt != None:
        request_data['user_assistant_prompt'] = user_assistant_prompt
    elif variables != None:
        request_data['variables'] = variables

    # オプションのクエリパラメータの構築
    request_params = {
        "stream": stream  # TrueまたはFalse
    }

    # リクエスト先のURLの構築
    request_URL = (f"{GPT_Mangaer_URL}/requst/openai-post/{prompt_name}")

    # httpxの非同期クライアントを使用して、60秒のタイムアウトを持つ非同期リクエストを行う
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(request_URL, json=data, params=params)
        
        # 以下のコメントアウトされたprint文は、リクエストの結果をコンソールに表示するためのもの
        # print(f"Request_GPT < ID:{ID} > \nmessage:{print_responce}\njson:{data}\n")
        
        # IDとレスポンステキストを含む辞書を返す
        return {"ID": ID, "message": response.text}

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
    finder = AnswerFinder(directory,streamer_vector_path)
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
    recording_swicth = await get_data_from_server(f"{AI_Tuber_URL}/mic_recording_bool/get/")
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
                    await post_data_from_server(post_data=[value],URL=f"{AI_Tuber_URL}/mic_recorded_list/post/")
            #print(f"結果: {result_data}")
            
        #関数を更新
        recording_swicth = await get_data_from_server(f"{AI_Tuber_URL}/mic_recording_bool/get/")
        whisper().change_recording_state(recording_swicth)
        await asyncio.sleep(0)

def process1():
    #Whisper modelの準備
    print("Create Whisper Model...",end='')
    model = whisper().create_whisper_model()
    print("Done.")
    asyncio.run(record_to_text(model))

async def Mirai_15_model():
    mirai_prompt_name = 'みらいV1.5'
    while True:
        mirai_prompt_data = await get_data_from_server(f"{GPT_Mangaer_URL}/prompts-get/lookup_prompt_by_name?prompt_name={mirai_prompt_name}")
        mirai_prompt_variables = mirai_prompt_data[0]['variables']
            

def process2_function():
    asyncio.run(Mirai_15_model())

if __name__ == "__main__":
    asyncio.run(Mirai_15_model())
    exit()

    #multiprocessing用プロセス作成
    process1 = multiprocessing.Process(target=process1)
    process2 = multiprocessing.Process(target=process2_function)

    #multiprocessingプロセス開始
    process1.start()
    process2.start()

    #process1.join()
    process2.join()