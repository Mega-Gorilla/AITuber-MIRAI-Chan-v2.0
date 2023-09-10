# speech_handler.py
import azure.cognitiveservices.speech as speechsdk
import os
import asyncio

class SpeechHandler:
    def __init__(self, speech_key, speech_region, language='ja-JP'):
        self.done = asyncio.Event()  # Use asyncio.Event to manage the state
        self.speech_key = speech_key
        self.speech_region = speech_region
        self.EndSilenceTimeoutMs = "1000"
        self.language = language
        self.speech_recognizer = None
        self.recognized_text = ""
        self.speech_state = None

    def end_speech(self):
        self.done.set()

    def _recognized_handler(self, evt):
        self.recognized_text = evt.result.text
        print(f'RECOGNIZED: {self.recognized_text}')
    
    def _speech_start_detected_handler(self, evt):
        self.speech_state = True
        print(f'SPEECH STARTED')

    def _speech_end_detected_handler(self, evt):
        self.speech_state = False
        print(f'SPEECH ENDED')

    async def from_mic(self):
        speech_config = speechsdk.SpeechConfig(subscription=self.speech_key, region=self.speech_region, speech_recognition_language=self.language)
        speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, self.EndSilenceTimeoutMs)
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        self.speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        self.speech_recognizer.session_started.connect(lambda evt: print('SESSION STARTED: {}'.format(evt)))
        self.speech_recognizer.session_stopped.connect(lambda evt: print('SESSION STOPPED {}'.format(evt)))
        self.speech_recognizer.recognized.connect(self._recognized_handler)
        self.speech_recognizer.speech_start_detected.connect(self._speech_start_detected_handler)
        self.speech_recognizer.speech_end_detected.connect(self._speech_end_detected_handler)

        self.speech_recognizer.start_continuous_recognition()

        print("Speak into your microphone.")
        
        await self.done.wait()  # Wait until self.done is set

        self.speech_recognizer.stop_continuous_recognition()

        return self.recognized_text, self.speech_state
    
async def main():
    handler = SpeechHandler(speech_key, speech_region)
    result_text, speech_state = await handler.from_mic()  # Wait for completion asynchronously

    print(f"Last recognized text: {result_text}, Final speech state: {speech_state}")

    # If you want to stop it at some point
    # handler.end_speech()

if __name__ == "__main__":
    speech_key = os.getenv("AZURE_API_KEY")
    speech_region = "japaneast"

    asyncio.run(main())