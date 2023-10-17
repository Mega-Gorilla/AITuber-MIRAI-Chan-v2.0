import os
import asyncio
from pydub import AudioSegment
import sounddevice as sd
import numpy as np
import wave
import time

async def GnenereteVoiceData(script, 
                             narrator="Koharu Rikka", 
                             saveCurrent_dir =os.path.join(os.path.dirname(os.path.abspath(__file__)), "wav"),
                             save_fileName = "output.wav",
                             exepath = "C:/Program Files/VOICEPEAK/voicepeak.exe", 
                             hightension=50, livid=50, lamenting=50, despising=50, narration=0):
    
    """
    任意のテキストからVoicePeak音声を生成保存します。この動作には5sから10sほどかかります。
    script: 読み上げるテキスト（文字列）
    narrator: ナレーターの名前（文字列）
    livid: ブチ切れの度合い
    lamenting: 嘆きの度合い
    despising: 蔑みの度合い
    narration: 楽しさの度合い
    """
    # 現在の実行しているファイルのパスを取得
    current_dir = saveCurrent_dir
    if not os.path.exists(current_dir):
        os.makedirs(current_dir)
    # wav出力先を現在のディレクトリに設定
    outpath = os.path.join(current_dir, save_fileName)
    # 引数を作成
    args = [
        exepath,
        "-s", script,
        "-n", narrator,
        "-o", outpath,
        "-e", f"hightension={hightension},livid={livid},lamenting={lamenting},despising={despising},narration={narration}"
    ]
    print(args)
    # プロセスを実行
    process = await asyncio.create_subprocess_exec(*args)
    # プロセスが終了するまで待機
    await process.communicate()

async def PlayVoiceData(audio_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "wav"),audio_fileName="output.wav",play_device_num=4):
    audio_path = os.path.join(audio_dir, audio_fileName)

    # 音声を再生
    with wave.open(audio_path, 'rb') as wf:
        samplerate = wf.getframerate()
        channels = wf.getnchannels()  # チャンネル数を取得
        data = wf.readframes(wf.getnframes())
        audio_int16 = np.frombuffer(data, dtype=np.int16)
        audio_float32 = audio_int16.astype(np.float32) / 32768.0  # int16 to float32 conversion
        if channels == 2:  # ステレオの場合
            audio_float32 = audio_float32.reshape(-1, 2)

    # 指定したデバイスで音声を再生
    with sd.OutputStream(samplerate=samplerate, channels=channels, device=chosen_device) as stream:
        stream.write(audio_float32)

    # wavファイルを削除
    print(f"remove: {audio_path}")
    #os.remove(audio_path)

def get_audio_devices():
    """
    Get a list of available audio devices.

    Returns:
    - devices: A list of dictionaries. Each dictionary represents an audio device.
    """
    devices = sd.query_devices()
    print(devices)
    return devices

async def main(chosen_device):
    sentences = [
    "こんにちわ",
    "ねえ、きいて！",
    "昨日のドラマ見た？",
    "この服、どう思う？",
    "新しいネイルしたのよ。",
    "ランチ、一緒に行こう？",
    "もう、今日のテスト難しい！",
    "あの先生、また長話しだった。",
    "このバッグ、新しくて可愛いでしょ？",
    "明日の放課後、カフェ行く？",
    "週末、ショッピングモールに行こうよ。",
    "最近、新しい彼氏できたんだって？",
    "あの子、ちょっと噂話してるの知ってる？",
    "私、ダイエット始めたんだ。応援してね！",
    "ねえ、この間の合宿、楽しかったよね？",
    "明日の数学の授業、予習した？全然できない。",
    "あのイケメン先輩、私と目が合った気がするんだよね。",
    "週末のパーティー、何の服着ていく？選べないよー。",
    "この化粧品、最新のやつなんだよ。少し高いけど、効果あるみたい。",
    "最近、髪の毛がパサつくから、良いトリートメント探してるんだけど、何かオススメある？",
    "昨日の夜、夢の中であの先輩とデートしてたの。超リアルで、目が覚めたときがっかりしたよ。",
    "この前、友達とカラオケ行ったんだけど、新しい歌上手く歌えたの。また行こうよ、一緒に！",
    "先週の学園祭、みんなでダンスしたの楽しかったよね。来年も参加する？どんなダンスしようか考え中。",
    "最近の悩みっていうか、将来どうなりたいのか分からないの。みんなはどうやって進路決めてるのかな。",
    "私、最近流行りのこのマンガにハマってて、毎晩読んでるんだよ。次の巻が待ち遠しい！おすすめしたい！"
    ]

    for sentence in sentences:

        # 音声データを生成
        await GnenereteVoiceData(sentence)
        # 音声データを再生
        await PlayVoiceData(play_device_num=chosen_device)

if __name__ == "__main__":
    get_audio_devices()
    chosen_device = int(input("Enter the device index to use for playback: "))
    asyncio.run(main(chosen_device))