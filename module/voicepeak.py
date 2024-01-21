import os
import asyncio
import sounddevice as sd
import wave
import aiofiles

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
    livid: ブチ切れの度合い (0%-100%)
    lamenting: 嘆きの度合い (0%-100%)
    despising: 蔑みの度合い (0%-100%)
    narration: 楽しさの度合い (0%-100%)
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
    # プロセスを実行
    process = await asyncio.create_subprocess_exec(*args)
    # プロセスが終了するまで待機
    await process.communicate()

    #再生秒数を計算
    #duration = await get_wav_duration(outpath)
    duration =100

    print(f"save {save_fileName}")
    return  round(duration * 100) / 100

async def get_wav_duration(filename):
    async with aiofiles.open(filename, 'rb') as af:
        # aiofilesを使用してファイルデータを読み込む
        file_data = await af.read()

    # wave.openを使ってファイル情報を取得
    with wave.open(filename, 'rb') as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        duration = frames / float(rate)
        return duration

def get_audio_devices():
    """
    Get a list of available audio devices.

    Returns:
    - devices: A list of dictionaries. Each dictionary represents an audio device.
    """
    devices = sd.query_devices()
    print(devices)
    return devices

async def main():
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
    result = []
    for sentence in sentences:
        # 音声データを生成
        time_data = asyncio.create_task(GnenereteVoiceData(sentence,save_fileName=f"{sentence}.wav"))
        result.append(time_data)
    
    await asyncio.gather(*asyncio.all_tasks())
    print(result)

if __name__ == "__main__":
    asyncio.run(main())