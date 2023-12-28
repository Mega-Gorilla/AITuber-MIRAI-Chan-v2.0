
from rich import print
import asyncio
import httpx
from httpx import ConnectError, HTTPStatusError, TooManyRedirects, RequestError, NetworkError
try:
    from module.rich_desgin import error
except ImportError:
    from rich_desgin import error

# 非同期関数としてデータをPOSTするための関数
async def post_data_from_server(URL,post_data=None,post_params=None,max_retries=3, delay=1, timeout=60.0):
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
            if post_data != None:
                if isinstance(post_data, (dict, list)):  # post_dataが辞書型またはリスト型の場合
                    request_kwargs["json"] = post_data
                else:  # それ以外の場合、生のデータとして扱う
                    request_kwargs["data"] = post_data
                # クエリパラメータをリクエストに追加
            if post_params is not None:
                request_kwargs["params"] = post_params
            # httpxの非同期クライアントを使用して非同期的なリクエストを行う
            async with httpx.AsyncClient(timeout=timeout) as client:
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
        response = None
        try:
            # httpxの非同期クライアントを使用して非同期的なリクエストを行う
            async with httpx.AsyncClient(max_redirects=max_retries) as client:
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
        except TooManyRedirects as e:
            # リダイレクトの最大数を超えた場合は、エラーメッセージを表示して、Noneを返す
            error("Too Many Redirects:", f"{e}", {"Mode":"Get","URL": URL,"Request Count":retries})
            return None
        except RequestError as e:
            error("Request Error:", f"{e}", {"Mode":"Get","URL": URL,"Request Count":retries})
            retries += 1
            await asyncio.sleep(delay)
        except NetworkError as e:
            error("NetworkError:", f"{e}", {"Mode":"Get","URL": URL,"Request Count":retries})
            retries += 1
            await asyncio.sleep(delay)
        except Exception as e:
            # 上記以外のエラーが発生した場合は、エラーメッセージを表示して、Noneを返す
            error("An error occurred:", f"{e}", {"Mode":"Get","URL": URL,"Request Count":retries,"Responce_data":response})
            retries += 1
            await asyncio.sleep(delay)

# GPTにリクエストするための非同期関数
async def request_GPT(ID,URL, prompt_name, user_assistant_prompt=None, variables=None, stream=False):
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
    request_URL = (f"{URL}/requst/openai-post/{prompt_name}")

    # httpxの非同期クライアントを使用して、60秒のタイムアウトを持つ非同期リクエストを行う
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await post_data_from_server(request_URL,request_data,request_params)
        
        # 以下のコメントアウトされたprint文は、リクエストの結果をコンソールに表示するためのもの
        # print(f"Request_GPT < ID:{ID} > \nmessage:{print_responce}\njson:{data}\n")
        
        # IDとレスポンステキストを含む辞書を返す
        return {"ID": ID, "message": response.text}