# azuer_speech_handler.py
import azure.cognitiveservices.speech as speechsdk
import os
import asyncio
from rich import print

class SpeechHandler:
    def __init__(self, queue, producer_id,speech_key, speech_region, language='ja-JP',mic_id=None,TimeoutMs='3000',debug=True):
        self.done = False
        self.speech_key = speech_key
        self.speech_region = speech_region
        self.device_ID = mic_id
        self.EndSilenceTimeoutMs = TimeoutMs
        self.language = language
        self.speech_recognizer = None
        self.result_text = ""
        self.queue = queue
        self.debug = debug
        self.producer_id = producer_id
        
    def _recognized_handler(self, evt):
        self.result_text = evt.result.text
        if self.result_text !="":
            self.done=True
        if self.debug:
            print(f'RECOGNIZED: {evt.result.text}')
    
    def session_started(self, evt):
        self.result_text = ""
        self.done = False

    async def from_mic(self):
        speech_config = speechsdk.SpeechConfig(subscription=self.speech_key, region=self.speech_region, speech_recognition_language=self.language)
        speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, self.EndSilenceTimeoutMs)
        if self.device_ID != None:
            audio_config = speechsdk.audio.AudioConfig(device_name=str(self.device_ID))
            if self.debug:
                print(f"setup mic id {self.device_ID}")
        else:
            if self.debug:
                print(f"defaltmic {self.device_ID}")
            audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        
        self.speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        #self.speech_recognizer.session_stopped.connect(lambda evt: print('SESSION STOPPED {}'.format(evt)))
        #self.speech_recognizer.canceled.connect(lambda evt: print('SESSION STOPPED {}'.format(evt)))
        self.speech_recognizer.recognized.connect(self._recognized_handler)
        self.speech_recognizer.session_started.connect(self.session_started)
        
        print("[green]Speak into your microphone.[/green]")

        self.speech_recognizer.start_continuous_recognition()
        while not self.done:
            await asyncio.sleep(0.5)
        
        print("[red]Azure Speech Stopped..[/red]")
            
        self.speech_recognizer.stop_continuous_recognition()
        await self.queue.put({"ID":self.producer_id,"message":self.result_text})

async def handle_results(queue):
    while True:
        result = await queue.get()
        print(f"Received result: {result}")
        queue.task_done()

async def main():
    queue = asyncio.Queue()
    handler = SpeechHandler(queue,speech_key, speech_region)

    # Start a task to handle results
    asyncio.create_task(handle_results(queue))

    while True:
        asyncio.create_task(handler.from_mic())
        await asyncio.sleep(1)

if __name__ == "__main__":
    speech_key = os.getenv("AZURE_API_KEY")
    speech_region = "japaneast"

    asyncio.run(main())