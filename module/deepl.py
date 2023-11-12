
import aiohttp
import asyncio
import os

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

async def main():
    text = await atranslate_text(os.getenv("DEEPL_API_KEY"),"The mark of the immature man is that he wants to die nobly for a cause, while the mark of the mature man is that he wants to live humbly for one.")
    print(text)

if __name__ == "__main__":
    asyncio.run(main())