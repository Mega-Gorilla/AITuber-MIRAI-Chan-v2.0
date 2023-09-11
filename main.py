#main.py
from azure_speech_handler import SpeechHandler
from rich import print
import os
import openai
import asyncio

#keys
azure_key = os.getenv("AZURE_API_KEY")
speech_region = "japaneast"
openai.api_key = os.getenv("OPENAI_API_KEY")

async def handle_results(queue):
    while True:
        result = await queue.get()
        print(f"Received result: {result}")
        queue.task_done()

async def main():
    queue = asyncio.Queue()
    handler = SpeechHandler(queue,speech_key, speech_region)

    # Start a task to handle results
    asyncio.create_task(handle_results(queue))

    while True:
        asyncio.create_task(handler.from_mic())
        await asyncio.sleep(1)

if __name__ == "__main__":
    speech_key = os.getenv("AZURE_API_KEY")
    speech_region = "japaneast"

    asyncio.run(main())