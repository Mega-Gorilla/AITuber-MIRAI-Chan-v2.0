import asyncio
import httpx  # 非同期HTTPクライアント
import os,csv


async def post_data_to_server(base_url, endpoint, data):
    full_url = base_url.rstrip('/') + '/' + endpoint.lstrip('/')  # URLを結合
    async with httpx.AsyncClient() as client:  # 非同期HTTPクライアントのインスタンスを作成
        response = await client.post(full_url, json=data)  # 非同期でPOSTリクエストを実行
    return response

async def get_data_from_server(base_url, endpoint):
    full_url = base_url.rstrip('/') + '/' + endpoint.lstrip('/')  # URLを結合
    async with httpx.AsyncClient() as client:
        response = await client.get(full_url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get data. Status code: {response.status_code}")
            return None

async def get_files_with_extension(directory, extension):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, find_files_with_extension, directory, extension)

def find_files_with_extension(directory, extension):
    extension_files = [os.path.splitext(os.path.basename(f))[0] for f in os.listdir(directory) if f.endswith(extension)]
    return extension_files

#フォルダ内のanimファイルを取得しCSVに存在しないanimがあった場合csvに追加する。
async def update_csv_file(directory,csv_file_name):
    #ディレクトリ内のaimファイルリストを取得
    anim_files = await get_files_with_extension(directory, ".anim")
    #CSVファイルのaimリストを取得
    existing_filenames = read_existing_filenames_from_csv(os.path.join(directory, csv_file_name))
    new_files = [filename for filename in anim_files if filename not in list(existing_filenames.keys())]
    if new_files:
            append_to_csv(os.path.join(directory, csv_file_name), new_files)

async def update_csv_column(directory,csv_file_name, search_str, replacement_str):
    # CSVファイルを読み込む
    with open(os.path.join(directory, csv_file_name), 'r', newline='', encoding='utf-8') as file:
        rows = list(csv.reader(file))
        
    # 文字列Aに一致する行を検索し、文字列Bで2列目を更新する
    for row in rows:
        if row[0] == search_str:
            if len(row) > 1:
                row[1] = replacement_str
            else:
                row.append(replacement_str)
            
    # 更新したデータでCSVファイルを書き戻す
    with open(os.path.join(directory, csv_file_name), 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(rows)

def read_existing_filenames_from_csv(csv_filename):
    with open(csv_filename, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        # ヘッダー行をスキップ
        next(reader, None)  # None を指定して、ファイルに行がない場合のエラーを避ける
        # 1列目をキー、2列目を値として辞書を作成
        return {row[0]: row[1] if len(row) > 1 else "" for row in reader}


def append_to_csv(csv_filename, filenames):
    with open(csv_filename, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for filename in filenames:
            writer.writerow([filename])

async def wait_until_done_or_timeout(base_url, endpoint, timeout=30):
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
    anim_files = await get_files_with_extension(directory, ".anim")
    print(f"フォルダ内にあるanimファイル: {anim_files}")

    #update CSV
    csv_filename = "anim_description.csv"
    await update_csv_file(directory,csv_filename)

    #Get CSV Data
    csv_data = read_existing_filenames_from_csv(os.path.join(directory, csv_filename))
    filtered_dict = {}
    empty_value_dict = {}
    for key, value in csv_data.items():
        if value != "":
            filtered_dict[key] = value
        else:
            empty_value_dict[key] = value
    print(f"説明があるanimファイル: {filtered_dict}")
    print(f"説明がないanimファイル: {empty_value_dict}")

    for key, value in empty_value_dict.items():
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
        await update_csv_column(directory,csv_filename,key,input_data)

if __name__ == "__main__":
    asyncio.run(main())