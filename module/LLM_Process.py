import requests,asyncio

"""
本スクリプトは、LLM問合せ後の処理がプロンプトごとに記載されています。
どのプロンプトに対してどの関数が対応しているかは、main.py LLM_config.function_mapを参照のこと
"""

class config:
    #URL
    GPT_Mangaer_URL = "http://127.0.0.1:8000"
    AI_Tuber_URL = "http://127.0.0.1:8001"

class LLM:
    total_token_summary_trigger = {"gpt-4-1106-preview":3171,"gpt-4":6143}
    completion_token_summary_trigger = {"gemini-pro":6144}

async def process_airi_v17(request_id):
    """
    アイリ v17向け処理関数
    Streamのみ対応
    """
    content = ""
    done = False
    #切り取りマーカーリスト
    markers = [["# Organize Your Thoughts:","#Result:"],["# Organize Your Thoughts:","# Result:"],["statements:","voice quality:"],["voice quality:","gesture:"],["gesture:","statements:"],["gesture:","--<Done>--"]]
    content_list = []
    
    while True:
        request = requests.get(f"{config.GPT_Mangaer_URL}/LLM/get-chunk/?reset_all=false&del_request_id={request_id}").json()
        #request = await get_data_from_server(URL=f"{config.GPT_Mangaer_URL}/LLM/get-chunk/?reset_all=false&del_request_id={request_id}")
        for item in request:
            content += item['content']
            if item['finish_reason']=="Done":
                content += "\n--<Done>--"
                done = True
        
        # レスポンス結果より必要なデータを抜き出し
        for start_marker, end_marker in markers:
            if start_marker in content and end_marker in content:
                # 開始と終了のインデックスを見つける
                start_index = content.find(start_marker) + len(start_marker)
                end_index = content.find(end_marker)
                item = content[start_index:end_index].strip()
                if item == '':
                    continue

                if start_marker == "statements:":
                    #会話ログへの追加
                    requests.post(url=f"{config.AI_Tuber_URL}/talk_log/post",json={"アイリ":item})

                content_list.append({start_marker:item})
                #表示した内容を受信したデータから消去する
                content = content[end_index:]
                print(f"{start_marker} {item}")
        
        if done:
            break
        await asyncio.sleep(0.2)
    print("AITuber 会話データ:")
    print(content_list)

    #Check Tokens
    while True:
        request = requests.get(f"{config.GPT_Mangaer_URL}/LLM/get/?reset=false&del_request_id={request_id}").json()
        if len(request)==0:
            await asyncio.sleep(1)
            continue
        else:
            model_name = request[0]['model']
            if 'gpt' in model_name:
                if request[0]['total_tokens'] < LLM.total_token_summary_trigger[model_name]:
                    break
            elif 'gemini' in model_name:
                if request[0]['completion_tokens'] < LLM.completion_token_summary_trigger[model_name]:
                    break
            #要約フラグ作成
            print("ログを要約します")
            requests.post(f"{config.AI_Tuber_URL}/LLM/request/post/?prompt_name=talk_logTosummary&stream=false")
            #ゲームプレイ中は、ゲームログ要約も実施
            if requests.get(f"{config.AI_Tuber_URL}/GameName/get")!= "":
                requests.post(f"{config.AI_Tuber_URL}/LLM/request/post/?prompt_name=game_logTosummary&stream=false")

    await asyncio.sleep(1)
    print("process_airi_v17 = Done.")

async def process_talk_logTosummary(request_id):
    request = requests.get(f"{config.GPT_Mangaer_URL}/LLM/get/?reset_all=false&del_request_id={request_id}").json()
    summary = request[0]['content']
    requests.post(f"{config.GPT_Mangaer_URL}/summary/post?summary={summary}")
    await asyncio.sleep(1)

async def process_game_logTosummary(request_id):
    request = requests.get(f"{config.GPT_Mangaer_URL}/LLM/get/?reset_all=false&del_request_id={request_id}").json()
    summary = request[0]['content']
    requests.post(f"{config.GPT_Mangaer_URL}/GameData/summary/post?summary={summary}")
    await asyncio.sleep(1)