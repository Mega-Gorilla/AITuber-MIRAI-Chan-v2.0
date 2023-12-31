import requests

class config:
    #URL
    GPT_Mangaer_URL = "http://127.0.0.1:8000"
    AI_Tuber_URL = "http://127.0.0.1:8001"

async def request_talk_logTosummary():
    #要約向けデータを取得
    talk_log = requests.get(f"{config.AI_Tuber_URL}/talk_log/get?reset=false")
    summary = requests.get(f"{config.AI_Tuber_URL}/summary/get")
    str_talk_log = ""
    for d in talk_log:
        key, value = list(d.items())[0]
        str_talk_log += f"{key} -> {value}\n"
    
    return {"talk_log":talk_log,"old_talk_log":summary}

async def request_game_logTosummary():
    #ゲーム要約用データを取得
    talk_log = requests.get(f"{config.AI_Tuber_URL}/GameData/talk_log/get?reset=false")
    summary = requests.get(f"{config.AI_Tuber_URL}/GameData/summary/get")
    game_info = requests.get(f"{config.AI_Tuber_URL}/GameData/GameInfo/get")
    game_log_str = ""
    for d in talk_log:
        key, value = list(d.items())[0]
        game_log_str += f"{key} -> {value}\n"
    
    return {"game_log":game_log_str,"old_game_log":summary,"game_info":game_info}