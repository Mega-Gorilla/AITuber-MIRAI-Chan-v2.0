
import asyncio
import sys
from module.server_requests import *
from faster_whisper import WhisperModel
import numpy as np
import sounddevice as sd

class config:
    AI_Tuber_URL = "http://127.0.0.1:8001"
    recorded_buffer = np.empty((0, 1), dtype='float32')
    recorded_length = []
    whisper_model = None

def create_whisper_model(model_size = "large-v2", device="cuda", compute_type="int8_float32"):
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    config.whisper_model = model
    return model

async def audio_to_text(language='ja',beam_size=5):
        
        segments, info = config.whisper_model.transcribe(config.recorded_buffer, beam_size=beam_size,language=language)
        return segments, info

async def check_mic_mute(event, check_interval=0.3):
    while not event.is_set():
        if await get_data_from_server(f"{config.AI_Tuber_URL}/mic_mute/get/"):
            event.set()
            break
        await asyncio.sleep(check_interval)

async def record_buffer(buffer, samplerate=44100, **kwargs):
    loop = asyncio.get_event_loop()
    event = asyncio.Event()
    idx = 0

    def callback(indata, frame_count, time_info, status):
        nonlocal idx
        if status:
            print(status)
        remainder = len(buffer) - idx
        if remainder <= 0:
            loop.call_soon_threadsafe(event.set)
            raise sd.CallbackStop
        indata = indata[:remainder]
        buffer[idx:idx + len(indata)] = indata
        idx += len(indata)

    stream = sd.InputStream(callback=callback, dtype=buffer.dtype, channels=buffer.shape[1], samplerate=samplerate, **kwargs)
    with stream:
        mic_mute_task = asyncio.create_task(check_mic_mute(event))
        await event.wait()
        mic_mute_task.cancel() #終了した場合タスクキャンセル
    # 実際に録音された長さにバッファのサイズを調整する
    recorded_buffer = buffer[:idx]  # idxは実際に録音されたフレーム数を指します
    config.recorded_buffer = np.concatenate((config.recorded_buffer,recorded_buffer), axis=0)
    
    config.recorded_length.append(idx)
    #return recorded_buffer, idx

async def play_buffer(buffer, samplerate=44100, **kwargs):
    loop = asyncio.get_event_loop()
    event = asyncio.Event()
    idx = 0

    def callback(outdata, frame_count, time_info, status):
        nonlocal idx
        if status:
            print(status)
        remainder = len(buffer) - idx
        if remainder == 0:
            loop.call_soon_threadsafe(event.set)
            raise sd.CallbackStop
        valid_frames = frame_count if remainder >= frame_count else remainder
        outdata[:valid_frames] = buffer[idx:idx + valid_frames]
        # Fill the rest of the output buffer with zeros if necessary
        outdata[valid_frames:] = 0
        idx += valid_frames

    # Set the samplerate for the OutputStream
    stream = sd.OutputStream(callback=callback, dtype=buffer.dtype,
                             channels=buffer.shape[1], samplerate=samplerate, **kwargs)
    with stream:
        await event.wait()

async def record_to_text(samplerate=44100):
    recode_max_buffer = calculate_buffer_size(samplerate=samplerate)
    if config.whisper_model == None:
        print("Create Whisper Model.")
        create_whisper_model()
        print("Whisper Model Create Done.")
    print('recording buffer ...')
    await record_buffer(recode_max_buffer, samplerate=samplerate)
    print('recording Done.')
    print(config.recorded_buffer.shape)
    segments, info= await audio_to_text()
    for segment in segments:
        #print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
        print("\033[92m{}\033[0m".format(segment.text))
    await post_data_from_server(f"{config.AI_Tuber_URL}/mic_mute/post/",{"mic_mute":False})

def calculate_buffer_size(seconds=300, samplerate=44100, channels=1):
    frames = seconds * samplerate
    return np.empty((frames, channels), dtype='float32')

async def main(samplerate=44100):
    buffer = calculate_buffer_size(samplerate=samplerate)
    print('recording buffer 1 ...')
    await record_buffer(buffer, samplerate=samplerate)
    await post_data_from_server(f"{config.AI_Tuber_URL}/mic_mute/post/",{"mic_mute":False})
    print('recording buffer 2 ...')
    await record_buffer(buffer, samplerate=samplerate)
    await post_data_from_server(f"{config.AI_Tuber_URL}/mic_mute/post/",{"mic_mute":False})
    print('recording buffer 3 ...')
    await record_buffer(buffer, samplerate=samplerate)
    #
    await play_buffer(config.recorded_buffer, samplerate=44100)
    print('Done playing.')

if __name__ == "__main__":
    try:
        asyncio.run(record_to_text())
    except KeyboardInterrupt:
        sys.exit('\nInterrupted by user')