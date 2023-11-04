import os
import csv
import pandas as pd
from joblib import dump, load
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from janome.tokenizer import Tokenizer

class AnswerFinder:
    def __init__(self):
        self.csv_list = None
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.tokenizer = Tokenizer()
        self.remove_words = ['、', '。', ' ','　','…']
    
    def create_or_load_vector_model(self, csv_directory, vetor_model_path):
        if self._is_new_csv_exists(csv_directory) or not os.path.isfile(vetor_model_path):
            csv_list = self._load_answers_from_directory(csv_directory)
            #不要な文字列を取り除く
            # 除外リストにない要素、かつ数字のみでない要素のみを新しいリストに含める
            self.csv_list = [item for item in csv_list if item not in self.remove_words and not item.isdigit()]
            self.tfidf_vectorizer = TfidfVectorizer(tokenizer=self.tokenize, stop_words=None)
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(csv_list)
            #Save Vector
            with open(vetor_model_path, 'wb') as f:
                # TfidfVectorizerの学習済み語彙とIDF値（inverse document frequency）を取得します。
                tfidf_vocabulary = self.tfidf_vectorizer.vocabulary_
                tfidf_idf = self.tfidf_vectorizer.idf_

                # モデルの状態とTF-IDF行列を保存します。
                # TfidfVectorizerのトークナイザーなど他の属性は保存されないため、ロード時に同じトークナイザーを指定する必要があります。
                dump({'str_':csv_list, 'vocabulary_': tfidf_vocabulary, 'idf_': tfidf_idf, 'matrix': self.tfidf_matrix}, f)
        else:
            self.load_vector_model(vetor_model_path)
    
    def load_vector_model(self, vetor_model_path):
        # モデルの状態をロードします。
        with open(vetor_model_path, 'rb') as f:
            model_data = load(f)
        
        # 新しいTfidfVectorizerインスタンスを初期化し、ロードした状態で更新します。
        self.tfidf_vectorizer = TfidfVectorizer(tokenizer=self.tokenize,
                                                stop_words=None,
                                                vocabulary=model_data['vocabulary_'])
        
        # idf_属性を復元します。
        self.tfidf_vectorizer.idf_ = model_data['idf_']
        
        # ロードしたTF-IDF行列をセットします。
        self.tfidf_matrix = model_data['matrix']

        #CSV文字列を復元します
        self.csv_list = model_data['str_']

    def save_tfidf_vectors_to_csv(self,csv_file_path):
        if self.tfidf_vectorizer is None or self.tfidf_matrix is None:
            print("TF-IDFベクトルがロードされていません。")
            return
        
        # 特徴名とインデックスの辞書を取得します。
        feature_names = self.tfidf_vectorizer.get_feature_names_out()
        
        # 各ドキュメントのTF-IDFベクトルを表示します。
        save_csv = []
        for doc_index, doc_vector in enumerate(self.tfidf_matrix):
            #print(f"Document {doc_index}:")
            # スパースベクトルを密なベクトルに変換し、重要な単語とスコアを表示します。
            dense_vector = doc_vector.todense().tolist()[0]
            scored_words = [(feature_names[word_index], score) for word_index, score in enumerate(dense_vector) if score > 0]
            for word, score in sorted(scored_words, key=lambda x: x[1], reverse=True):
                save_csv.append({"Word":word,"TF-IDF":score})
        with open(csv_file_path, 'w', newline='', encoding='utf_8_sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=save_csv[0].keys())
            writer.writeheader()
            writer.writerows(save_csv)

    def _is_new_csv_exists(self, csv_directory):
        # save_pathの更新時刻と、directory内のCSVファイルの更新時刻を比較
        if not os.path.exists(csv_directory):
            return True
        vector_time = os.path.getmtime(csv_directory)
        csv_files = [os.path.join(root, filename)
                     for root, dirs, files in os.walk(csv_directory)
                     for filename in files if filename.endswith('.csv')]
        for csv_file in csv_files:
            if os.path.getmtime(csv_file) > vector_time:
                return True
        return False

    def _load_answers_from_directory(self, directory):
        """
        directory以下のCSVファイルをソートし、CSVデータの配列を返す
        """
        csv_files = [os.path.join(root, filename)
                     for root, dirs, files in os.walk(directory)
                     for filename in files if filename.endswith('.csv')]
        answers = []
        for csv_file in csv_files:
            df = pd.read_csv(csv_file, skiprows=1)  # 最初の行をスキップ
            answers.extend(df.iloc[:, 0].tolist())
        return answers

    def find_similar(self, question, top_n=3):
        question_vector = self.tfidf_vectorizer.transform([question])
        cosine_similarities = linear_kernel(question_vector, self.tfidf_matrix).flatten()
        best_answer_indices = cosine_similarities.argsort()[-top_n:][::-1]
        return [(self.csv_list[i], cosine_similarities[i]) for i in best_answer_indices]
    
    def tokenize(self, text):
        return [token.surface for token in self.tokenizer.tokenize(text)]

if __name__ == '__main__':
    finder = AnswerFinder()
    finder.create_or_load_vector_model(csv_directory='memory/example_tone', vetor_model_path='memory/example_tone/streamer_vector.pkl')
    while True:
        print("endにて終了")
        serch_word = input("検索ワードを入力してください。:")
        if serch_word == 'end':
            break
        results = finder.find_similar(serch_word,5)
        for result in results:
            print(f'{result[0]} / {result[1]:.3f}')
    #csv_output_path = 'memory/tfidf_vectors.csv'
    #finder.save_tfidf_vectors_to_csv(csv_output_path)