#API.py
from module.azure_speech_handler import SpeechHandler
from rich import print
import os
import asyncio
import httpx

#keys
speech_key = os.getenv("AZURE_API_KEY")
speech_region = "japaneast"

#URL
BASE_URL = "http://127.0.0.1:8000"

class GlobalValues:
    UserName = "猩々博士"
    chara_profile="""みらい-女子高生ギャルAITuber。AIだが配信者をしている。
    博士-みらいの開発者。正体はゴリラ。"""
    talkFlag = False
    speechToText = True

def generate_table(history=5):
    return
#
async def post_data(data_dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/custom/add", json=data_dict)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to post data. Status code: {response.status_code}")
            return None

async def get_data():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/custom/get_data/")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get data. Status code: {response.status_code}")
            return None

#GPT Manager
#GPTにリクエストする
async def request_GPT(ID,prompt_name, user_prompt, variables,stream):
    data = {
        "user_assistant_prompt": user_prompt,
        "variables": variables
    }
    # オプションのクエリパラメータ
    params = {
        "stream": stream  # または True
    }
    request_URL = (f"{BASE_URL}/requst/openai-post/{prompt_name}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(request_URL, json=data, params=params)
        print_responce = response.text.replace('\n', '\n')
        #print(f"Request_GPT < ID:{ID} > \nmessage:{print_responce}\njson:{data}\n")
        return {"ID":ID,"message":response.text}
    
async def get_queue_request(url):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    except httpx.HTTPError as http_err:
        if http_err.response.status_code == 404:
            print("404 Error occurred. Stopping the loop.")
            return None
        else:
            print(f"An HTTP error occurred: {http_err}")
            return None
    except Exception as err:
        print(f"An error occurred: {err}")
        return None

# 処理結果に基づいて次のタスクを決定する
async def handle_results(result_queue,task_queue):
    chatLog=''
    chatLog_lineMax=6
    summary=''
    mirai_example=''
    summarize = False

    while True:

        #結果を取得する
        result = await result_queue.get()
        result_ID = result["ID"]
        result_message = result["message"]
        print_result_message = result_message.replace("\\n", "\n")
        print(f"結果ID:{result_ID} - Message:{print_result_message}\n")
        
        #グローバル関数更新
        global_dict = await get_data()
        if "talkFlag" in global_dict:
            GlobalValues.talkFlag = global_dict["talkFlag"]
            if GlobalValues.talkFlag:
                print("問い合わせON..")
        if "speechToText" in global_dict:
            GlobalValues.speechToText = global_dict["speechToText"]
        
        # User会話データがあった時、
        if result_ID == 'speech':
            #User 会話履歴の追加
            userTalkStr = result_message
            chatLog += (f"{GlobalValues.UserName}:{userTalkStr}\n")

            #メモリより類似会話の検索

            if GlobalValues.talkFlag: #Talkボタンが押された時
                GlobalValues.talkFlag = False

                miraichan_talk_task = request_GPT(ID="talkStr",
                                                  prompt_name='miraiV2',
                                                  user_prompt=[],
                                                  variables={
                                                      "chatLog":chatLog,
                                                        "summary":summary,
                                                        "mirai_example":mirai_example},
                                                    stream=True)
                #グローバル配列情報の更新
                global_dict = await get_data()
                global_dict["talkFlag"] = False
                await post_data(global_dict)
                #Jobを追加
                await task_queue.put(miraichan_talk_task)

        # Mirai Chan Talk が出力された時、
        if result_ID == 'talkStr':
            index_of_colon = result_message.index(":")
            # コロンの前の部分が10文字以下である場合、コロンを含めて削除
            if index_of_colon <= 10:
                result_message = result_message[index_of_colon+1:]
            
            #みらい　会話履歴の追加
            chatLog+=(f"Mirai:{result_message}\n")

        # 要約が出力されたとき、
        if result_ID == 'summaryStr':
            print(f"要約の実施\n{chatLog}->{result_message}")
            #要約変数に要約結果を追加
            summary = result_message
            #ショートメモリから要約した内容を消去
            chatlog_lines = chatLog.split("\n")
            chatLog = "\n".join(chatlog_lines[:-chatLog_lineMax])
            summarize = False

        # ショートメモリ(chatlog)が一定行数以上になった時要約を依頼
        if chatLog.count('\n')+1 > chatLog_lineMax and summarize == False:
            #ショートメモリが一定数以上になった時要約する
            summary_task = request_GPT(ID='summaryStr',
                                       prompt_name='talkSummary',
                                       user_prompt=[],
                                       variables={
                                                "charactor_profile":GlobalValues.chara_profile, 
                                                "summary":summary,
                                                "chat_log":chatLog},
                                        stream=True)
            summarize = True
            await task_queue.put(summary_task)
        
        await asyncio.sleep(0.1)

async def main():
    task_queue = asyncio.Queue()
    result_queue = asyncio.Queue()

    #azure setup
    handler = SpeechHandler(queue=result_queue,
                            producer_id="speech",
                            speech_key=speech_key, 
                            speech_region=speech_region,
                            TimeoutMs='1000',
                            debug=False)
    speech_task = None

    # Start a task to handle results
    asyncio.create_task(handle_results(result_queue,task_queue))
    
    async def wrapper(task):
        result = await task
        await result_queue.put(result)

    while True:
        global_dict = await get_data()

        if "talkFlag" in global_dict:
            GlobalValues.talkFlag = global_dict["talkFlag"]
        if "speechToText" in global_dict:
            GlobalValues.speechToText = global_dict["speechToText"]

        #Azure Speechが終了or実行されていない時、Speechを起動する。
        if  GlobalValues.speechToText and (speech_task is None or speech_task.done()):
            speech_task=asyncio.create_task(handler.from_mic())
        
        #新しいタスクを作成
        tasks_to_run = []

        while not task_queue.empty():
            task = await task_queue.get()
            tasks_to_run.append((task,))
        if tasks_to_run:
            # 定義に基づいてタスクを動的に生成
            tasks = [asyncio.create_task(wrapper(task)) for task, in tasks_to_run]
            #await asyncio.gather(*tasks)
            
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())