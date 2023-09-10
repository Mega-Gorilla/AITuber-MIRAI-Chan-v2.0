import azure.cognitiveservices.speech as speechsdk
from rich import print
import os
import openai

#keys
azure_key = os.getenv("AZURE_API_KEY")
speech_region = "japaneast"
openai.api_key = os.getenv("OPENAI_API_KEY")

#Azure_speech
def Azure_speech(speech_key,speech_region):
    #setting.
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region, speech_recognition_language='ja-JP')
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    speech_recognizer.recognized.connect(on_recognized)
    speech_recognizer.canceled.connect(on_canceled)
    speech_recognizer.session_started.connect(lambda evt: print('SESSION STARTED: {}'.format(evt)))
    speech_recognizer.session_stopped.connect(lambda evt: print('SESSION STOPPED {}'.format(evt)))
    speech_recognizer.start_continuous_recognition()

def on_recognized(args):
    recognized_text = args.result.text
    print(recognized_text)
def on_canceled(args):
    if args.reason == speechsdk.CancellationReason.Error:
        print(f"音声認識エラーが発生しました: {args.error_details}")

if __name__ == "__main__":
    Azure_speech(azure_key,speech_region)