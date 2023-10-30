from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Any

app = FastAPI()
class mic_setting:
    mic_recording_bool = False

class record_data:
    recorded_list = []

class AI_Tuber_setting:
    AI_talk_bool:bool = Field(default=False)

@app.post("/mic_recording_bool/post/")
def mic_post_item(mic_recodiong: bool):
    mic_setting.mic_recording_bool = mic_recodiong
    return mic_recodiong

@app.get("/mic_recording_bool/get/")
def mic_get_item():
    return mic_setting.mic_recording_bool

@app.post("/AI_talk_bool/post/")
def AI_talk_post_item(AI_talk: bool):
    AI_Tuber_setting.AI_talk_bool = AI_talk
    return AI_talk

@app.get("/AI_talk_bool/get/")
def AI_talk_get_item():
    return AI_Tuber_setting.AI_talk_bool

@app.post("/mic_recorded_list/post/")
def mic_recorded_dict_post(recorded_list: List[Any]):
    record_data.recorded_list.append(recorded_list)
    return record_data.recorded_list

@app.get("/mic_recorded_list/get/")
def mic_recorded_dict_get():
    responce_data = record_data.recorded_list
    record_data.recorded_list = []
    return responce_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)