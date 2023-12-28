from module.server_requests import *

class config:
    AI_Tuber_URL = "http://127.0.0.1:8001"
    #コメント参照個数
    comment_num = 4

async def get_youtube_comments_str():
    #Youtubeデータ取得
    new_comment_str = ""
    if await get_data_from_server(f"{config.AI_Tuber_URL}/youtube_api/chat_fetch/sw-get/"):
        new_comment_dict = await get_data_from_server(f"{config.AI_Tuber_URL}/youtube_api/chat_fetch/get/?reset=true")
        if new_comment_dict!=[]:
            comment_len=len(new_comment_dict)
            if config.comment_num < comment_len:
                comment_len = config.comment_num
            for i in range(comment_len):
                if new_comment_dict[i]['superchat_bool']:
                    new_comment_str += f"({new_comment_dict[i]['name']}:{new_comment_dict[i]['comment']} [Important Information: Received {new_comment_dict[i]['superchat_currency']}{new_comment_dict[i]['superchat_value']} super chat!!])"
                new_comment_str += f"({new_comment_dict[i]['name']}:{new_comment_dict[i]['comment']})"
        else:
            new_comment_str = "None."
    return new_comment_str

async def get_youtube_viewer_counts():
    viewer_count = await get_data_from_server(f"{config.AI_Tuber_URL}/youtube_api/viewer_count/")
    return viewer_count

async def get_youtube_subscriber_counts():
    subscriber_counts = await get_data_from_server(f"{config.AI_Tuber_URL}/youtube_api/subscriber_count/")
    return subscriber_counts