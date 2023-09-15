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

async def handle_results(result_queue,task_queue):
    gpt_instance = GPT_request()

    while True:
        result = await result_queue.get()
        #print(f"Received result: {result}")
        print(result["message"],end=None)
        if result["ID"] == 'speech':
            GPT_stream = gpt_instance.GPT_Stream(result_queue, 
                                                "GPT_stream", 
                                                os.getenv("OPENAI_API_KEY"), 
                                                Prompt=[{'system': gpt_instance.old_mirai_prompt()},{'user':result["message"]}],
                                                debug=True)
            await task_queue.put(["GPT_stream",GPT_stream])
        await asyncio.sleep(0.1)


async def main():
    task_queue = asyncio.Queue(maxsize=10)
    result_queue = asyncio.Queue(maxsize=100)

    handler = SpeechHandler(queue=result_queue,
                            producer_id="speech",
                            speech_key=speech_key, 
                            speech_region=speech_region,
                            TimeoutMs='1000',
                            debug=False)

    # Start a task to handle results
    receive_result_task=asyncio.create_task(handle_results(result_queue,task_queue))
    speech_task = None
    while True:
        if speech_task is None or speech_task.done():
            speech_task=asyncio.create_task(handler.from_mic())
            #job_manager.add_job("speech_task", speech_task)
        if task_queue.qsize()!=0:
            tasks= await task_queue.get()
            if asyncio.iscoroutine(tasks[1]):
                newjob = asyncio.create_task(tasks[1])
                job_manager.add_job(tasks[0],newjob)
            else:
                for task in tasks:
                    newjob = asyncio.create_task(task[1])
                    job_manager.add_job(task[0],newjob)
            
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    speech_key = os.getenv("AZURE_API_KEY")
    speech_region = "japaneast"

    asyncio.run(main())