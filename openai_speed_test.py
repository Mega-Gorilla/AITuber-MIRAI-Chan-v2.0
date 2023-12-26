import asyncio
from module.server_requests import *
import time
from openai import OpenAI

async def GPT_Manager(prompt_name,prompt_variables,stream,print_text = ""):
    prompt_name = prompt_name
    prompt_variables = prompt_variables
    process_time = time.time()
    await post_data_from_server(URL=f"http://127.0.0.1:8000/openai/request/?prompt_name={prompt_name}&stream_mode={stream}",post_data={"variables" : prompt_variables})
    requests = []
    while requests == []:
        requests = await get_data_from_server(URL=f"http://127.0.0.1:8000/openai/get/?reset=true")
    print(f"{print_text} ProcessTime: {time.time()-process_time}\nResult: {requests}")

async def OpenAI_API_test(model = "gpt-4-1106-preview",max_tokens=256,print_text = ""):
    process_time = time.time()
    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Describe the mooon in detail."}
        ],
        max_tokens= max_tokens
    )
    print(f"{print_text} ProcessTime: {time.time()-process_time}\nResult: {response}")

async def main():
    await GPT_Manager("Example_GPT4-turbo",{"question":"moon"},"false","gpt-4-1106-preview at GPTManager")
    await GPT_Manager("Example_GPT4",{"question":"moon"},"false","gpt-4 at GPTManager")
    await GPT_Manager("Example_GPT4",{"question":"moon"},"true","gpt-4 Stream at GPTManager")
    await OpenAI_API_test(print_text= "gpt-4-1106-preview at OpenAI API")
    await OpenAI_API_test(model= "gpt-4",print_text= "gpt-4 at OpenAI API")

if __name__ == "__main__":
    asyncio.run(main())