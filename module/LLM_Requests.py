from server_requests import *

class config:
    #URL
    GPT_Mangaer_URL = "http://127.0.0.1:8000"

async def airi_v16(request_id):
    request = await get_data_from_server(URL=f"{config.GPT_Mangaer_URL}/LLM/get-chunk/?reset=true")
