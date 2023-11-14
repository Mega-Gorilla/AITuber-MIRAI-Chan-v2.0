
import aiohttp
import asyncio
import requests
import os
from openai import OpenAI

async def atranslate_text(deepl_key,text, target_language='JA',source_language='EN'):
    
    endpoint = 'https://api-free.deepl.com/v2/translate'

    # 翻訳リクエストのパラメータ
    params = {
        'auth_key': deepl_key,
        'text': text,
        'target_lang': target_language,
        'source_lang': source_language
    }

    # aiohttp.ClientSessionを使用してリクエストを非同期で実行
    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, data=params) as response:
            # レスポンスをJSONとして解析
            result = await response.json()
            return result['translations'][0]['text']

def translate_text(deepl_key, text, target_language='JA', source_language='EN'):
    endpoint = 'https://api-free.deepl.com/v2/translate'

    # 翻訳リクエストのパラメータ
    params = {
        'auth_key': deepl_key,
        'text': text,
        'target_lang': target_language,
        'source_lang': source_language
    }

    # requestsを使用してリクエストを実行
    response = requests.post(endpoint, data=params)

    # レスポンスをJSONとして解析
    result = response.json()
    return result['translations'][0]['text']

def translate_text_gpt3(openai_key, text, target_language='Japanese', source_language='English'):
    client = OpenAI(api_key=openai_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are an assistant who translates {source_language} into {target_language}."},
            {"role": "user", "content": text}
        ]
    )
    return response.dict()['choices'][0]['message']['content']

async def main():
    text = await atranslate_text(os.getenv("DEEPL_API_KEY"),"The mark of the immature man is that he wants to die nobly for a cause, while the mark of the mature man is that he wants to live humbly for one.")
    print(text)

if __name__ == "__main__":
    asyncio.run(main())