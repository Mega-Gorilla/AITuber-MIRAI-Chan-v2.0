from pydub import AudioSegment
from pydub.silence import split_on_silence
import pyaudio
from collections import deque
from faster_whisper import WhisperModel
import wave
import requests

class AudioProcessor:
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.rate = 48000
        self.channels = 2
        self.sample_format = pyaudio.paInt16
        self.frames_per_buffer = 2048
        self.stream = self.pa.open(
            format=self.sample_format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.frames_per_buffer
        )
        self.audio_buffer = deque(maxlen=self.rate * 30 * self.channels * 2 // self.frames_per_buffer)
        self.model = WhisperModel("large-v2", device="cuda")
    
    def process_stream(self):
        print("Mic Start")
        while True:
            try:
                audio_data = self.stream.read(self.frames_per_buffer, exception_on_overflow=False)
                self.audio_buffer.append(audio_data)
                response = requests.get("http://127.0.0.1:8001/mic_mute/get/")
                if response.text.lower() == 'true':
                    break
           
            except KeyboardInterrupt:
                print("処理を中断します。")
                break
    
    def save_buffer_to_file(self, file_path):
        # バッファ内の全データを結合
        audio_data_bytes = b''.join(self.audio_buffer)
        # 一時的なファイルに書き込む
        temp_file_path = "temp_audio.wav"
        with wave.open(temp_file_path, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(self.pa.get_sample_size(self.sample_format))
            wav_file.setframerate(self.rate)
            wav_file.writeframes(audio_data_bytes)
        
        # Pydubを使用して無音部分を削除する
        sound = AudioSegment.from_wav(temp_file_path)
        # 無音と見なす閾値と持続時間を調整する必要があります
        chunks = split_on_silence(sound, 
                                  min_silence_len=500,  # 無音の最小長さ（ミリ秒）
                                  silence_thresh=-40)  # 無音と見なす閾値（dB）

        # すべてのチャンクを結合して一つのオーディオにする
        combined = AudioSegment.empty()
        for chunk in chunks:
            combined += chunk
        
        # 結合したオーディオをファイルに保存
        combined.export(file_path, format="wav")
    
    def transcribe(self,audio_wav):
        segments, info = self.model.transcribe(audio_wav, beam_size=5, language='ja')
        for segment in segments:
            print("\033[92m{}\033[0m".format(segment.text))

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

# 使用例
audio_processor = AudioProcessor()
try:
    audio_processor.process_stream()
finally:
    print('mic end.')
    # 終了時にバッファをファイルに保存
    audio_processor.save_buffer_to_file('output.wav')
    audio_processor.transcribe('output.wav')
    audio_processor.close()
