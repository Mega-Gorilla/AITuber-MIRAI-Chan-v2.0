import csv,os
try:
    from module.deepl import translate_text
except ImportError:
    from deepl import translate_text,translate_text_gpt3

def translate_csv_column(csv_path, input_col, output_col, openai_key):
    """ CSVファイルの指定された列を翻訳して、結果を別の列に保存する """
    translated_data = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for i, row in enumerate(reader):
            if i == 0:
                # 項目行（ヘッダー）の処理
                translated_data.append(row)
            else:
                # データ行の処理
                try:
                    text_to_translate = row[input_col]
                    translated_text = translate_text_gpt3(openai_key, text_to_translate,'English','Japanese')
                    print(f"{text_to_translate} : {translated_text}")
                    # 出力列が存在するか確認し、必要に応じて拡張
                    if output_col >= len(row):
                        row.extend([''] * (output_col - len(row) + 1))
                    row[output_col] = translated_text
                except IndexError:
                    # インデックスが範囲外の場合のエラー処理
                    print(f"Error: Row {i} does not have column {input_col}")
                    continue
                translated_data.append(row)

    # 翻訳されたデータでCSVを上書き保存
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(translated_data)

def extract_and_write_columns(input_csv_path, column_indices, output_csv_path):
    """
    指定された列を読み込みCSVから抽出し、新しいCSVファイルに書き出す。

    :param input_csv_path: 読み込みCSVファイルのパス
    :param column_indices: 読み込む列のインデックスのリスト
    :param output_csv_path: 書き出し先CSVファイルのパス
    """
    with open(input_csv_path, mode='r', encoding='utf-8', newline='') as infile:
        reader = csv.reader(infile)
        with open(output_csv_path, mode='w', encoding='utf-8', newline='') as outfile:
            writer = csv.writer(outfile)
            for row in reader:
                selected_columns = [row[index] for index in column_indices]
                writer.writerow(selected_columns)

def csv_to_dict_array(input_csv_path, key_col_index, value_col_index):
    """
    CSVファイルを読み込み、指定された列をキーと値として辞書配列に変換する。
    最初の行（通常はヘッダー）は無視される。

    :param input_csv_path: 読み込みCSVファイルのパス
    :param key_col_index: キーとして使用する列のインデックス
    :param value_col_index: 値として使用する列のインデックス
    :return: 辞書配列
    """
    dict_array = []

    with open(input_csv_path, mode='r', encoding='utf-8', newline='') as infile:
        reader = csv.reader(infile)
        next(reader, None)  # 最初の行（ヘッダー）をスキップする
        for row in reader:
            key = row[key_col_index]
            value = row[value_col_index]
            dict_array.append({key: value})

    return dict_array

if __name__ == "__main__":
    openai_Key = os.environ.get("OPENAI_API_KEY")
    csv_path = r'C:\Users\hahah\OneDrive\Documents\AI\Mirai\Mirai-Unity\Assets\Resources\Animation\anim_description.csv'
    output_csv_path = r'C:\Users\hahah\OneDrive\Documents\AI\Mirai\AITuber-MIRAI-Chan-v2.0\memory\motion_list\train_data\motion_discription.csv'
    output_csv_path2 = r'C:\Users\hahah\OneDrive\Documents\AI\Mirai\AITuber-MIRAI-Chan-v2.0\memory\motion_list\motion.csv'

    translation_input=input('Translation y/n: ')
    if translation_input == 'y' or translation_input == 'Y':
        translate_csv_column(csv_path, 1,2,openai_Key)
    #extract_and_write_columns(csv_path,[2],output_csv_path)
    #extract_and_write_columns(csv_path,[0,2],output_csv_path2)
    print(csv_to_dict_array(output_csv_path2,0,1))
    