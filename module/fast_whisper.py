from pydub import AudioSegment
from pydub.silence import split_on_silence
import pyaudio
from collections import deque
from faster_whisper import WhisperModel
import wave
import requests
import time

class AudioProcessor:
    def __init__(self):
        self.URL = "http://127.0.0.1:8001"
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

    def play_wav_file(self, file_path):
        # WAVファイルを開く
        wf = wave.open(file_path, 'rb')

        # 再生用のストリームを開く
        stream = self.pa.open(
            format=self.pa.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True
        )

        # ファイルからデータチャンクを読み込み、再生する
        data = wf.readframes(self.frames_per_buffer)
        while data:
            stream.write(data)
            data = wf.readframes(self.frames_per_buffer)

        # ストリームを閉じる
        stream.stop_stream()
        stream.close()

        # ファイルを閉じる
        wf.close()

    def process_stream(self):
        print("Mic Start")
        while True:
            try:
                audio_data = self.stream.read(self.frames_per_buffer, exception_on_overflow=False)
                self.audio_buffer.append(audio_data)
                response = requests.get(f"{self.URL}/mic_mute/get/")
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
        segment_data = []
        if list[segments] == []:
            segment_data = ["He is keeping his mouth shut."]
        else:
            for segment in segments:
                print("\033[92m{}\033[0m".format(segment.text))
                segment_data.append(segment.text)
        response = requests.post(
            f'{self.URL}/mic_recorded_list/post/',
            json=segment_data
        )

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

    def stop(self):
        self.stream.stop_stream()
    def start(self):
        self.stream.start_stream()

    def reset(self):
        self.audio_buffer = deque(maxlen=self.rate * 30 * self.channels * 2 // self.frames_per_buffer)

if __name__ == "__main__":
    audio_processor = AudioProcessor()
    try:
        while requests.get(f"{audio_processor.URL}/Program_Fin_bool/get/").text.lower() == 'false':
            response = requests.get(f"{audio_processor.URL}/mic_mute/get/")
            if response.text.lower() == 'false':
                audio_processor.process_stream()
                # process_stream()が正常に終了したら、バッファをファイルに保存し、書き起こしを行う
                print('mic end.')
                audio_processor.stop()
                audio_processor.save_buffer_to_file('output.wav')
                audio_processor.reset()
                audio_processor.start()
                audio_processor.transcribe('output.wav')
                audio_processor.play_wav_file('output.wav')
            else:
                time.sleep(1)
            
    except Exception as e:
        # ここでエラーを処理する
        print(f"予期せぬエラーが発生しました: {e}")
    finally:
        # 終了時に必ずリソースをクリーンアップ
        audio_processor.close()