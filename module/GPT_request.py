#GPT_request.py
import tiktoken
import openai
import asyncio
import time,sys,os
from rich import print
try:
    from module.rich_desgin import error
except ImportError:
    from rich_desgin import error

class GPT_request:
    def talknizer(self,texts):
        tokens = tiktoken.get_encoding('gpt2').encode(texts)
        return len(tokens)

    def GPT_error_list(self):
        gpt_error_mapping = {
            openai.error.APIError: ("OpenAI API Error", "しばらく時間をおいてからリクエストを再試行し、問題が解決しない場合は弊社までご連絡ください。", 'sleep'),
            openai.error.Timeout: ("OpenAI Timeout Error", "リクエストがタイムアウトしました。しばらく時間をおいてからリクエストを再試行し、問題が解決しない場合は弊社までご連絡ください。", 'sleep'),
            openai.error.RateLimitError: ("OpenAI Rate Limit Error", "リクエストのペースを上げてください。詳しくはレート制限ガイドをご覧ください。", 'exit'),
            openai.error.APIConnectionError: ("OpenAI API Connection Error", "ネットワーク設定、プロキシ設定、SSL証明書、またはファイアウォールルールを確認してください。", 'exit'),
            openai.error.InvalidRequestError: ("OpenAI API Invalid Request Error", "エラーメッセージは、具体的なエラーについてアドバイスするはずです。呼び出している特定のAPIメソッドのドキュメントを確認し、有効で完全なパラメータを送信していることを確認してください。また、リクエストデータのエンコーディング、フォーマット、サイズを確認する必要があるかもしれません。", 'exit'),
            openai.error.AuthenticationError: ("OpenAI Authentication Error", "APIキーまたはトークンを確認し、それが正しく、アクティブであることを確認してください。アカウントダッシュボードから新しいものを生成する必要があるかもしれません。", 'exit'),
            openai.error.ServiceUnavailableError: ("OpenAI Service Unavailable Error", "しばらく時間をおいてからリクエストを再試行し、問題が解決しない場合はお問い合わせください。ステータスページをご確認ください。", 'sleep')
        }
        return gpt_error_mapping
    
    async def add_to_queue(self,queue, producer_id, content):
        await queue.put({"ID": producer_id, "message": content})

    async def GPT_request_stream(self,queue, producer_id, OpenAI_key,Prompt=[{"system":"You are a helpful assistant."},{"user":"Hello!"}],temp=0,tokens_max=2000,model="gpt-4",max_retries=3,debug=False):
        openai.api_key=OpenAI_key
        if debug:
            print(f'Start {producer_id}: {model}')
        #OpenAIのエラーリスト
        gpt_error_mapping = self.GPT_error_list()

        Prompts=[]
        for original_dict in Prompt:
            transformed_dict = {}
            for key, value in original_dict.items():
                transformed_dict["role"] = key
                transformed_dict["content"] = value
            Prompts.append(transformed_dict)

        retry_count = 0

        while retry_count < max_retries:
            try:
                result_content=""
                gpt_result = openai.ChatCompletion.create(
                    model=model,
                    messages=Prompts,
                    stream=True,
                    temperature=temp,
                    max_tokens=tokens_max,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0
                )
                for chunk in gpt_result:
                    #print(f"\n{chunk}\n")
                    content = chunk["choices"][0].get("delta", {}).get("content")
                    fin_reason = chunk["choices"][0].get("finish_reason")
                    if content is not None or fin_reason != "stop":
                        result_content += content
                        await queue.put({"id": producer_id, 
                                         "message": content,
                                         "index": chunk["choices"][0].get("index"),
                                         'id':chunk["id"],
                                         'object':chunk["object"],
                                         'created':chunk["created"],
                                         'model':chunk["model"],
                                         "finish_reason": fin_reason})
                        await asyncio.sleep(0.01)
                    else:
                        #token calc
                        prompt_tokens=self.talknizer(''.join([item['content'] for item in Prompts]))
                        completion_tokens=self.talknizer(result_content)
                        await queue.put({"id": producer_id, 
                                         "message": result_content,
                                         "index": chunk["choices"][0].get("index"),
                                         'id':chunk["id"],
                                         'object':chunk["object"],
                                         'created':chunk["created"],
                                         'model':chunk["model"],
                                         "finish_reason": fin_reason,
                                         "prompt_tokens":prompt_tokens,
                                         "completion_tokens":completion_tokens,
                                         "total_tokens":prompt_tokens+completion_tokens})
                        await asyncio.sleep(0.01)
                break
            except Exception as e:
                title, message, action = gpt_error_mapping.get(type(e), ("OpenAI Unknown Error", "不明なエラーです。", 'exit'))
                print(e)
                e=str(e)+(f"\n\nRaw Prompt: {Prompt}\nProcessed Prompt: {Prompts}\nTemp: {temp}\nMax Tokens: {tokens_max}")
                error(title, message, e if action == 'exit' else None)
                
                if action == 'exit':
                    sys.exit(1)
                elif action == 'sleep':
                    await asyncio.sleep(1)
    
    async def GPT_request(self,queue, producer_id, OpenAI_key,Prompt=[{"system":"You are a helpful assistant."},{"user":"Hello!"}],temp=0,tokens_max=2000,model="gpt-4",max_retries=3,debug=False):
        openai.api_key=OpenAI_key
        if debug:
            print(f'Start {producer_id}: {model}')
        #OpenAIのエラーリスト
        gpt_error_mapping = self.GPT_error_list()

        Prompts=[]
        for original_dict in Prompt:
            transformed_dict = {}
            for key, value in original_dict.items():
                transformed_dict["role"] = key
                transformed_dict["content"] = value
            Prompts.append(transformed_dict)

        retry_count = 0

        while retry_count < max_retries:
            try:
                response = openai.ChatCompletion.create(
                model=model,
                messages=Prompts,
                temperature=temp,
                max_tokens=tokens_max,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
                )
                await queue.put({"id": producer_id, 
                                    "message": response["choices"][0]["message"]["content"],
                                    "index": response["choices"][0].get("index"),
                                    'id':response["id"],
                                    'object':response["object"],
                                    'created':response["created"],
                                    'model':response["model"],
                                    "finish_reason": response["choices"][0].get("finish_reason"),
                                    "prompt_tokens":response["usage"].get("prompt_tokens"),
                                    "completion_tokens":response["usage"].get("completion_tokens"),
                                    "total_tokens":response["usage"].get("total_tokens")})
                await asyncio.sleep(0.5)
                break

            except Exception as e:
                title, message, action = gpt_error_mapping.get(type(e), ("OpenAI Unknown Error", "不明なエラーです。", 'exit'))
                print(e)
                e=str(e)+(f"\n\nRaw Prompt: {Prompt}\nProcessed Prompt: {Prompts}\nTemp: {temp}\nMax Tokens: {tokens_max}")
                error(title, message, e if action == 'exit' else None)
                
                if action == 'exit':
                    sys.exit(1)
                elif action == 'sleep':
                    await asyncio.sleep(1)

async def handle_results(queue):
    while True:
        result = await queue.get()
        print(f"Received result: {result}")
        queue.task_done()

async def main():
    queue = asyncio.Queue()
    
    gpt_instance = GPT_request()
    GPT_stream = gpt_instance.GPT_request_stream(queue, "GPT_stream", os.getenv("OPENAI_API_KEY"), model="gpt-3.5-turbo",Prompt=[{'system': "あなたは女子高生ギャルをロールプレイしてください"},{'user':"こんばんわ"}],temp=0)
    GPT_Request = gpt_instance.GPT_request(queue, "GPT_stream", os.getenv("OPENAI_API_KEY"), model="gpt-3.5-turbo",Prompt=[{'system': "あなたは女子高生ギャルをロールプレイしてください"},{'user':"こんばんわ"}],temp=0)

    consumer_task = asyncio.create_task(handle_results(queue))
    producer_task1 = GPT_stream
    producer_task2 = GPT_Request
    
    starttime=time.time()
    await producer_task1
    print(f"Stream Result Time:{time.time()-starttime}")
    starttime=time.time()
    await producer_task2
    print(f"Normal Result Time:{time.time()-starttime}")

    await queue.join()

    consumer_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())