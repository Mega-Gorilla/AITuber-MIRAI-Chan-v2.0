#API.py
from module.azure_speech_handler import SpeechHandler
from rich import print
from fastapi import FastAPI
import os
import asyncio
import time
import httpx

#keys
speech_key = os.getenv("AZURE_API_KEY")
speech_region = "japaneast"

#URL
openai_post = "http://127.0.0.1:8000/requst/openai-post"
openai_get = "http://127.0.0.1:8000/requst/openai-get/queue"

#global
UserName = "猩々博士"
talkFlag = False
speechToText = True

#FastAPI
app = FastAPI()
@app.post("/request/genereteTalk",tags=["Request"])
async def TalkJob_request():
    global talkFlag
    talkFlag = True
    return{"/request/genereteTalk":talkFlag}

@app.post("/request/speechToText",tags=["Request"])
async def speechToText_request():
    global speechToText
    speechToText = not speechToText
    return{"/request/speechToText":speechToText}

#GPT Manager
async def request_GPT(prompt_name, user_prompt, variables,stream):
    data = {
        "user_assistant_prompt": user_prompt,
        "variables": variables
    }
    # オプションのクエリパラメータ
    params = {
        "stream": stream  # または True
    }
    request_URL = (f"{openai_post}/{prompt_name}")
    
    print(data)
    async with httpx.AsyncClient() as client:
        response = await client.post(request_URL, json=data, params=params)
        return {"ID":'talkStr',"message":response}
    
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

#新しいasyncioタスクを作成するプロセス
async def create_tasks(task_queue):
    #新しいタスクを作成
    if task_queue.qsize()!=0:
        tasks= await task_queue.get()
        if asyncio.iscoroutine(tasks[1]):
            newjob = asyncio.create_task(tasks[1])
            job_manager.add_job(tasks[0],newjob)
        else:
            for task in tasks:
                newjob = asyncio.create_task(task[1])
                job_manager.add_job(task[0],newjob)

# result_queueを監視し、新しい関数が入力されたら処理するプロセス
#handle_resultsは無限ループする。
async def handle_results(result_queue,task_queue):
    chatLog=''
    summary=''
    mirai_example=''

    while True:
        result = await result_queue.get()
        #print(f"Received result: {result}")
        print(result["message"],end=None)
        
        if result["ID"] == 'speech':
            #User 会話履歴の追加
            userTalkStr=result['message']
            chatLog += (f"{UserName}:{userTalkStr}\n")

            #メモリより類似会話の検索

            if talkFlag: #Talkボタンが押された時
                global talkFlag
                talkFlag = False

                miraiChanTalkStr= await request_GPT(prompt_name='miraiV2.json',
                                  user_prompt=[],
                                      variables={
                                          "chatLog":chatLog,
                                          "summary":summary,
                                          "mirai_example":mirai_example},
                                          stream=True)
                #みらい　会話履歴の追加
                chatLog+=(f"Mirai:{miraiChanTalkStr}\n")
                result_queue.put(miraiChanTalkStr)
        
        
        await asyncio.sleep(0.1)

async def main():
    task_queue = asyncio.Queue(maxsize=10)
    result_queue = asyncio.Queue(maxsize=100)

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

    while True:
        
        #Azure Speechが終了or実行されていない時、Speechを起動する。
        if  speechToText and (speech_task is None or speech_task.done()):
            speech_task=asyncio.create_task(handler.from_mic())
        
        await create_tasks(task_queue)
            
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())