#API.py
from module.azure_speech_handler import SpeechHandler
from module.GPT_request import GPT_request
from test_async import test_async
from job_manager import JobManager
from rich import print
from fastapi import FastAPI
from pydantic import BaseModel
import os
import openai
import asyncio
import time

#keys
azure_key = os.getenv("AZURE_API_KEY")
speech_region = "japaneast"
openai_key = os.getenv("OPENAI_API_KEY")

#FastAPI
app = FastAPI()
job_manager = JobManager()

#Get Job Status
@app.get("/jobs/{job_name}")
async def read_job_status(job_name: str):
    return {job_name: job_manager.get_status(job_name)}
#Get job list
@app.get("/job_list/")
async def read_job_list():
    return job_manager.get_job_list()

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

async def Create_StreamGPT_task(task_queue,result_queue,producer_id,openai_key,prompt,temp=1,tokens_max=2000,model_name='gpt-4',max_retries=3,debug=False):
    gpt_instance = GPT_request()
    GPT_stream = gpt_instance.GPT_Stream(result_queue, 
                                        producer_id, 
                                        openai_key, 
                                        prompt,
                                        temp,
                                        tokens_max,
                                        model_name,
                                        max_retries,
                                        debug)
    await task_queue.put(["GPT_stream",GPT_stream])

# result_queueを監視し、新しい関数が入力されたら処理するプロセス
async def handle_results(result_queue,task_queue):
    speech_str=''
    last_speech_time=time.time()

    while True:
        result = await result_queue.get()
        #print(f"Received result: {result}")
        print(result["message"],end=None)
        
        if result["ID"] == 'speech':
            if time.time()-last_speech_time > job_manager.auto_speech_delay: #一定時間経過した場合の読み上げ
                await Create_StreamGPT_task(task_queue,result_queue,'mirai_talk',openai_key,)

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
    process_result_task=asyncio.create_task(handle_results(result_queue,task_queue))
    job_manager.add_job("process_result_task",process_result_task)

    while True:

        if speech_task is None or speech_task.done():
            speech_task=asyncio.create_task(handler.from_mic())
            job_manager.add_job("speech_task", speech_task)
        
        await create_tasks(task_queue)
            
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    speech_key = os.getenv("AZURE_API_KEY")
    speech_region = "japaneast"

    asyncio.run(main())