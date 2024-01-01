import requests,asyncio
from module.youtube_api import *

class config:
    #URL
    GPT_Mangaer_URL = "http://127.0.0.1:8000"
    AI_Tuber_URL = "http://127.0.0.1:8001"

class airi_v17_config:
    viewer_count = 0
    subscriber_count = 0
    tone_example_top_n = 3


async def request_talk_logTosummary():
    #要約向けデータを取得
    talk_log = requests.get(f"{config.AI_Tuber_URL}/talk_log/get?reset=false").json()
    summary = requests.get(f"{config.AI_Tuber_URL}/summary/get").json()
    str_talk_log = ""
    for d in talk_log:
        key, value = list(d.items())[0]
        str_talk_log += f"{key} -> {value}\n"
    await asyncio.sleep(0)
    return {"talk_log":talk_log,"old_talk_log":summary}

async def request_game_logTosummary():
    #ゲーム要約用データを取得
    talk_log = requests.get(f"{config.AI_Tuber_URL}/GameData/talk_log/get?reset=false").json()
    summary = requests.get(f"{config.AI_Tuber_URL}/GameData/summary/get").json()
    game_info = requests.get(f"{config.AI_Tuber_URL}/GameData/GameInfo/get").json()
    game_log_str = ""
    for d in talk_log:
        key, value = list(d.items())[0]
        game_log_str += f"{key} -> {value}\n"
    await asyncio.sleep(0)
    return {"game_log":game_log_str,"old_game_log":summary,"game_info":game_info}

async def get_mic_recorded_str():
    #マイク文字列の取得
    mic_recorded_list = requests.get(f"{config.AI_Tuber_URL}/mic_recorded_list/get/?reset=true").json()
    if mic_recorded_list == []:
        result = ""
    else:
        result = '\n'.join([' '.join(item) for item in mic_recorded_list])
    await asyncio.sleep(0)
    return result

async def request_airi_v17():

    mirai_prompt_name = 'airi_v17'
    #みらいプロンプトに必要な関数情報を取得
    mirai_prompt_data = requests.get(f"{config.GPT_Mangaer_URL}/prompts-get/lookup_prompt_by_name?prompt_name={mirai_prompt_name}").json()
    mirai_prompt_variables = mirai_prompt_data['variables']
    
    #Youtubeデータ取得
    new_comment_str = await get_youtube_comments_str()
    new_viewer_count = await get_youtube_viewer_counts()
    new_subscriber_count = await get_youtube_subscriber_counts()

    viewer_count = "No Data."
    if new_viewer_count['ok']==True:
        if airi_v17_config.viewer_count == new_viewer_count['viewer_count']:
            viewer_count = f"{new_viewer_count['viewer_count']} (Viewership Change: 0)"
        else:
            viewer_count = f"{new_viewer_count['viewer_count']} (Viewership Change: {new_viewer_count['viewer_count']-airi_v17_config.viewer_count})"
        airi_v17_config.viewer_count = new_viewer_count['viewer_count']

    subscriber_count = "No Data."
    if new_subscriber_count['ok']==True:
        if airi_v17_config.subscriber_count == new_subscriber_count['subscriber_count']:
            subscriber_count = f"{new_subscriber_count['subscriber_count']} (Subscriber Change: 0)"
        else:
            subscriber_count = f"{new_subscriber_count['subscriber_count']} (Subscriber Change: {new_subscriber_count['subscriber_count']-airi_v17_config.subscriber_count})"
        airi_v17_config.subscriber_count = new_subscriber_count['subscriber_count']
    
    #Speech to Text文章を取得
    mic_recorded_str = await get_mic_recorded_str()
    if mic_recorded_str != "":
        requests.post(f"{config.AI_Tuber_URL}/talk_log/post",json={"博士":mic_recorded_str})

    if mic_recorded_str != "":
    #類似会話例を取得
        serch_tone_word = mic_recorded_str.split('\n')[0]
        streamer_tone_dict = requests.get(f"{config.AI_Tuber_URL}/tone_similar/get/?str_dialogue={serch_tone_word}&top_n={airi_v17_config.tone_example_top_n}").json()
        streamer_tone = ''
        for d in streamer_tone_dict:
            if 'ok' in d:
                if d['ok']==False:
                    streamer_tone = 'None'
            elif 'text' in d:
                streamer_tone+=d['text']+"\n"
    else:
        streamer_tone = ""

    #会話ログを作成
    talk_log = ""
    talk_log_list = requests.get(f"{config.AI_Tuber_URL}/talk_log/get?reset=false").json()
    if talk_log_list != []:
        for d in talk_log_list:
            key, value = list(d.items())[0]
            talk_log += f"{key} -> {value}\n"
        talk_log = talk_log.rstrip('\n')
    
    #Summaryの取得
    stream_summary = requests.get(f"{config.AI_Tuber_URL}/summary/get").json()
    
    #Showrunner_adviceの取得
    showrunner_advice = requests.post(f"{config.AI_Tuber_URL}/Showrunner_Advice/post/?mic_end=false").json()

    #game_infoを取得
    other_streaming_info = ""
    game_title = requests.get(f"{config.AI_Tuber_URL}/GameName/get").json()
    if game_title != "":
        game_log = await get_data_from_server(URL=f"{config.AI_Tuber_URL}/GameData/talk_log/get?reset=false")
        game_log_str = ""
        for d in game_log:
            key = d["name"]
            value = d["text"]
            game_log_str += f"{key} -> {value}\n"
        game_log_str = game_log_str.rstrip('\n')
        game_summary = requests.get(f"{config.AI_Tuber_URL}/GameData/summary/get").json()
        game_info = requests.get(f"{config.AI_Tuber_URL}/GameData/GameInfo/get").json()
        other_streaming_info = "\n"+game_info + "\n\nSummary content of the game information being played:\n" + game_summary + "\n\nGame Logs:\n" + game_log_str


    mirai_prompt_variables = {
        "example_tone": streamer_tone,
        "stream_summary": stream_summary,
        "talk_logs": talk_log,
        "subscribers_num": subscriber_count,
        "viewers_num": viewer_count,
        "viewer_comments": new_comment_str,
        "Showrunner_advice": showrunner_advice,
        "other_streaming_info": other_streaming_info
    }
    await asyncio.sleep(0)
    return mirai_prompt_variables


async def request_airi_v17_gemini():

    mirai_prompt_name = 'airi_v17_gemini'
    #みらいプロンプトに必要な関数情報を取得
    mirai_prompt_data = requests.get(f"{config.GPT_Mangaer_URL}/prompts-get/lookup_prompt_by_name?prompt_name={mirai_prompt_name}").json()
    mirai_prompt_variables = mirai_prompt_data['variables']
    
    #Youtubeデータ取得
    new_comment_str = await get_youtube_comments_str()
    new_viewer_count = await get_youtube_viewer_counts()
    new_subscriber_count = await get_youtube_subscriber_counts()

    viewer_count = "No Data."
    if new_viewer_count['ok']==True:
        if airi_v17_config.viewer_count == new_viewer_count['viewer_count']:
            viewer_count = f"{new_viewer_count['viewer_count']} (Viewership Change: 0)"
        else:
            viewer_count = f"{new_viewer_count['viewer_count']} (Viewership Change: {new_viewer_count['viewer_count']-airi_v17_config.viewer_count})"
        airi_v17_config.viewer_count = new_viewer_count['viewer_count']

    subscriber_count = "No Data."
    if new_subscriber_count['ok']==True:
        if airi_v17_config.subscriber_count == new_subscriber_count['subscriber_count']:
            subscriber_count = f"{new_subscriber_count['subscriber_count']} (Subscriber Change: 0)"
        else:
            subscriber_count = f"{new_subscriber_count['subscriber_count']} (Subscriber Change: {new_subscriber_count['subscriber_count']-airi_v17_config.subscriber_count})"
        airi_v17_config.subscriber_count = new_subscriber_count['subscriber_count']
    
    #Speech to Text文章を取得
    mic_recorded_str = await get_mic_recorded_str()
    if mic_recorded_str != "":
        requests.post(f"{config.AI_Tuber_URL}/talk_log/post",json={"博士":mic_recorded_str})

    #会話ログを作成
    talk_log = ""
    talk_log_list = requests.get(f"{config.AI_Tuber_URL}/talk_log/get?reset=false").json()
    if talk_log_list != []:
        for d in talk_log_list:
            key, value = list(d.items())[0]
            talk_log += f"{key} -> {value}\n"
        talk_log = talk_log.rstrip('\n')
    
    #Summaryの取得
    stream_summary = requests.get(f"{config.AI_Tuber_URL}/summary/get").json()
    
    #Showrunner_adviceの取得
    showrunner_advice = requests.post(f"{config.AI_Tuber_URL}/Showrunner_Advice/post/?mic_end=false").json()

    #game_infoを取得
    other_streaming_info = ""
    game_title = requests.get(f"{config.AI_Tuber_URL}/GameName/get").json()
    if game_title != "":
        game_log = await get_data_from_server(URL=f"{config.AI_Tuber_URL}/GameData/talk_log/get?reset=false")
        game_log_str = ""
        for d in game_log:
            key = d["name"]
            value = d["text"]
            game_log_str += f"{key} -> {value}\n"
        game_log_str = game_log_str.rstrip('\n')
        game_summary = requests.get(f"{config.AI_Tuber_URL}/GameData/summary/get").json()
        game_info = requests.get(f"{config.AI_Tuber_URL}/GameData/GameInfo/get").json()
        other_streaming_info = "\n"+game_info + "\n\nSummary content of the game information being played:\n" + game_summary + "\n\nGame Logs:\n" + game_log_str


    mirai_prompt_variables = {
        "stream_summary": stream_summary,
        "talk_logs": talk_log,
        "subscribers_num": subscriber_count,
        "viewers_num": viewer_count,
        "viewer_comments": new_comment_str,
        "Showrunner_advice": showrunner_advice,
        "other_streaming_info": other_streaming_info
    }
    await asyncio.sleep(0)
    return mirai_prompt_variables