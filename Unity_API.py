import asyncio
import httpx  # 非同期HTTPクライアント
import os,csv

async def post_data_to_server(base_url, endpoint, data):
    """
    指定したサーバーのエンドポイントにデータを非同期的にPOSTします。

    :param base_url: サーバーのベースURL
    :param endpoint: データをPOSTするエンドポイント
    :param data: POSTするデータ
    :return: httpxのレスポンスオブジェクト
    """
    full_url = base_url.rstrip('/') + '/' + endpoint.lstrip('/')  # URLを結合
    async with httpx.AsyncClient() as client:  # 非同期HTTPクライアントのインスタンスを作成
        response = await client.post(full_url, json=data)  # 非同期でPOSTリクエストを実行
    return response

async def get_data_from_server(base_url, endpoint):
    """
    指定したサーバーのエンドポイントからデータを非同期的にGETします。

    :param base_url: サーバーのベースURL
    :param endpoint: データを取得するエンドポイント
    :return: エンドポイントから取得したデータのJSONオブジェクト、またはエラーの場合はNone
    """
    full_url = base_url.rstrip('/') + '/' + endpoint.lstrip('/')  # URLを結合
    async with httpx.AsyncClient() as client:
        response = await client.get(full_url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get data. Status code: {response.status_code}")
            return None

async def get_files_with_extension(directory, extension):
    """
    指定したディレクトリ内の特定の拡張子を持つファイルの名前を非同期に取得します。

    :param directory: ファイルを検索するディレクトリのパス
    :param extension: 検索するファイルの拡張子（例：'.txt'）
    :return: 指定された拡張子を持つファイルの名前のリスト
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, find_files_with_extension, directory, extension)

def find_files_with_extension(directory, extension):
    """
    指定したディレクトリ内の特定の拡張子を持つファイルの名前を取得します。

    :param directory: ファイルを検索するディレクトリのパス
    :param extension: 検索するファイルの拡張子（例：'.txt'）
    :return: 指定された拡張子を持つファイルの名前のリスト
    """
    extension_files = [os.path.splitext(os.path.basename(f))[0] for f in os.listdir(directory) if f.endswith(extension)]
    return extension_files

def csv_to_dict(csv_path, key_col, value_col):
    """
    CSVファイルから、指定されたKey列とValue列を使用して辞書を作成します。
    
    :param csv_path: CSVファイルのパス
    :param key_col: Keyとして使用する列の名前
    :param value_col: Valueとして使用する列の名前
    :return: 作成された辞書
    """
    result_dict = {}
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row[key_col]
            value = row[value_col]
            result_dict[key] = value
            
    return result_dict

def update_dict_from_list(dict_a, list_b):
    """
    辞書配列Aのkey文字列と配列Bの文字列を比較して、一致しない文字列が配列Bにある時、
    その文字列をKeyとして辞書配列Aに加える。その際の追加したKeyのValueは""とする。

    :param dict_a: 元の辞書
    :param list_b: 比較する文字列のリスト
    :return: 更新された辞書
    """
    for item in list_b:
        if item not in dict_a:
            dict_a[item] = ""

    return dict_a

async def update_csv_from_dict(csv_path, dict_data, value_colname):
    """
    CSVファイルの指定された列を、辞書のキーに基づいて更新します。
    :param csv_path: 更新するCSVファイルのパス
    :param dict_data: キーと更新する値を持つ辞書
    :param value_colname: 更新するCSVの列名
    :return: None
    """
    rows = []

    # CSVデータを読み込む
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row[value_colname] in dict_data:
                row[value_colname] = dict_data[row[value_colname]]
            rows.append(row)
    
    # CSVデータを更新して書き込む
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

async def wait_until_done_or_timeout(base_url, endpoint, timeout=30):
    """
    指定したサーバーのエンドポイントからデータを非同期的に取得し、
    'animation' キーが存在する場合、そのキーの値だけ待機します。
    'animation' キーが存在しない場合、指定したタイムアウト時間まで待機します。

    :param base_url: サーバーのベースURL
    :param endpoint: データを取得するためのエンドポイント
    :param timeout: タイムアウトするまでの最大待機時間（秒）
    """
    start_time = asyncio.get_running_loop().time()
    while True:
        response = await get_data_from_server(base_url, endpoint)
        if "animation" in response:
            wait_second = response.get("animation")
            print(wait_second)
            await asyncio.sleep(wait_second)
            break
        
        # 経過時間のチェック
        elapsed_time = asyncio.get_running_loop().time() - start_time
        if elapsed_time > timeout:
            print("Timed out waiting for 'animation':'Done'.")
            break
        
        # ここで1秒のスリープを挟むことも可能
        await asyncio.sleep(1)

async def main():
    directory = "C:\\Users\\MegaGorilla\\Documents\\Unity\\VRM Motion\\Assets\\Resources\\Animation"
    csv_filename = "anim_description.csv"

    anim_files = await get_files_with_extension(directory, ".anim")
    print(f"フォルダ内にあるanimファイル: {anim_files}")

    #CSVデータを辞書配列で取得
    csv_dictionary = csv_to_dict(os.path.join(directory, csv_filename),'ファイル名','説明')
    #辞書配列とフォルダ内animファイルを比較して、辞書配列に存在しないanimファイル名をkeyとして辞書配列に追加
    dictionary = update_dict_from_list(csv_dictionary,anim_files)

    filtered_dict = {}
    for key, value in dictionary.items():
        if value == "":
            filtered_dict[key] = value
    print(f"説明がないanimファイルが見つかりました:\n {filtered_dict}")

    for key, value in filtered_dict.items():
        data = {
            "VRM_expression": "Neutral",
            "VRM_animation": key
        }
        print(f"アニメーション名： {key}")
        while True:
            #アニメーションリクエスト
            await post_data_to_server("http://127.0.0.1:8000", "custom/add/B", data)
            #アニメーションが終了するまで待機(タイムアウト30秒)
            await wait_until_done_or_timeout("http://127.0.0.1:8000", "custom/get_data/B")
            input_data = input("アニメーションの説明を代入してください:\n")
            if input_data !="":
                break
        await update_csv_from_dict(os.path.join(directory, csv_filename),{key:input_data},"説明")

if __name__ == "__main__":
    asyncio.run(main())