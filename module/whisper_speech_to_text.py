from faster_whisper import WhisperModel
import sounddevice as sd
import numpy as np
import asyncio
import wave
import io

class speech_to_text:
    def __init__(self):
        self.SAMPLE_RATE = 44100
        self.CHANNELS = 2
        self.DTYPE = np.int16
        self.THRESHOLD = 500  # 無音判定のしきい値
        self.SILENCE_DURATION = 0.4 * self.SAMPLE_RATE  # 0.5秒
        self.recording_state = {"is_recording": True}

    def create_whisper_model(self,model_size = "large-v2", device="cuda", compute_type="float16"):
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        return model

    def audio_to_bytesio(self,audio_data, sample_rate, channels=2, sampwidth=2):
        # Create a BytesIO object
        output = io.BytesIO()

        # Use the wave module to write the audio data to the BytesIO object
        with wave.open(output, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sampwidth)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())

        # Reset the position of the BytesIO object to the beginning
        output.seek(0)

        return output

    def noise_gate(self,data, threshold):
        return np.where(np.abs(data) > threshold, data, 0)

    def amplify(self, data, factor=2.0):
        """ Amplify the volume of the audio data. """
        amplified = data * factor
        # Avoid clipping
        amplified = np.clip(amplified, np.iinfo(self.DTYPE).min, np.iinfo(self.DTYPE).max)
        return amplified.astype(self.DTYPE)

    async def record_audio(self,audio_queue):
        loop = asyncio.get_event_loop()
        buffer = []
        silent_samples = 0
        is_sound_detected = False  # 音が検出されたかどうかのフラグ

        with sd.InputStream(samplerate=self.SAMPLE_RATE, channels=self.CHANNELS) as stream:
            print("Start Recording..")
            while self.recording_state["is_recording"]:
                audio_chunk, overflowed = await loop.run_in_executor(None, lambda: stream.read(self.SAMPLE_RATE))
                audio_chunk = audio_chunk * (2**15)  # 16-bit PCM
                audio_chunk = audio_chunk.astype(self.DTYPE)

                # フィルタ処理
                audio_chunk = self.noise_gate(audio_chunk, self.THRESHOLD)

                # 初めての音声検出
                if not is_sound_detected and np.abs(audio_chunk).mean() > self.THRESHOLD:
                    is_sound_detected = True

                if is_sound_detected:
                    buffer.extend(audio_chunk)
                    await asyncio.sleep(0)

                    # 無音部分の検出
                    if np.abs(audio_chunk).mean() < self.THRESHOLD:
                        silent_samples += len(audio_chunk)
                    else:
                        silent_samples = 0

                    # 1秒以上の無音があればバッファをキューに追加してリセット
                    if silent_samples > self.SILENCE_DURATION:
                        arr = np.array(buffer)
                        await audio_queue.put(arr)
                        await asyncio.sleep(0)
                        buffer = []
                        silent_samples = 0
                        is_sound_detected = False
        return
    
    async def audio_to_text(self,wav,model,language='ja',beam_size=5):
        segments, info = model.transcribe(wav, beam_size=beam_size,language=language)
        return segments, info
    
    async def process_audio(self, audio_queue, text_queue, model):
        loop = asyncio.get_event_loop()
        while self.recording_state["is_recording"]:
            if audio_queue.qsize()==0:
                await asyncio.sleep(1)
                continue
            audio_data = await audio_queue.get()
            amplified_audio = self.amplify(audio_data, 2.0)  # Amplify by a factor of 2
            audio_bytesio = await loop.run_in_executor(None, lambda: self.audio_to_bytesio(amplified_audio, self.SAMPLE_RATE))
            await asyncio.sleep(0.2)
            segments, info = await self.audio_to_text(audio_bytesio, model,beam_size=5)
            await asyncio.sleep(0)
            for segment in segments:
                #print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
                print(segment.text)
                await text_queue.put(segment.text)
                await asyncio.sleep(0)
        return

    def mic_to_text_retun_task(self, model, audio_queue, text_queue):
        recorder_task = self.record_audio(audio_queue)
        audio_to_text_task = self.process_audio(audio_queue, text_queue, model)
        return recorder_task, audio_to_text_task

    async def mic_to_text_async(model,queue):
        
        return

async def main():
    print(speech_to_text().recording_state)
    audio_queue = asyncio.Queue()
    text_queue = asyncio.Queue()
    model = speech_to_text().create_whisper_model()
    recorder_task, audio_to_text_task = speech_to_text().mic_to_text_retun_task(model, audio_queue, text_queue)
    recorder_task = asyncio.create_task(recorder_task)
    audio_to_text_task = asyncio.create_task(audio_to_text_task)
    await asyncio.gather(recorder_task, audio_to_text_task)
    result = await text_queue.get()
    print(result)

if __name__ == "__main__":
    asyncio.run(main())