import os
import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from janome.tokenizer import Tokenizer

class AnswerFinder:
    def __init__(self, directory, save_path='data/vector.pkl'):
        # Janomeのトークナイザーを初期化
        self.tokenizer = Tokenizer()
        self.save_path = save_path
        
        # 保存されたベクトルがある場合、それをロード。なければ新しく生成
        if self._is_new_csv_exists(directory):
            self.answers = self._load_answers_from_directory(directory)
            self.tfidf_vectorizer = TfidfVectorizer(tokenizer=self.tokenize, stop_words=None)
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.answers)
            # ベクトルを保存
            with open(self.save_path, 'wb') as f:
                pickle.dump((self.answers, self.tfidf_matrix, self.tfidf_vectorizer), f)
        else:
            with open(self.save_path, 'rb') as f:
                self.answers, self.tfidf_matrix, self.tfidf_vectorizer = pickle.load(f)

    def _is_new_csv_exists(self, directory):
        # save_pathの更新時刻と、directory内のCSVファイルの更新時刻を比較
        if not os.path.exists(self.save_path):
            return True
        vector_time = os.path.getmtime(self.save_path)
        csv_files = [os.path.join(root, filename)
                     for root, dirs, files in os.walk(directory)
                     for filename in files if filename.endswith('.csv')]
        for csv_file in csv_files:
            if os.path.getmtime(csv_file) > vector_time:
                return True
        return False

    def _load_answers_from_directory(self, directory):
        csv_files = [os.path.join(root, filename)
                     for root, dirs, files in os.walk(directory)
                     for filename in files if filename.endswith('.csv')]

        answers = []
        for csv_file in csv_files:
            df = pd.read_csv(csv_file, skiprows=1)  # 最初の行をスキップ
            answers.extend(df.iloc[:, 0].tolist())

        return answers

    def tokenize(self, text):
        return [token.surface for token in self.tokenizer.tokenize(text)]

    def find_similar(self, question, top_n=3):
        question_vector = self.tfidf_vectorizer.transform([question])
        cosine_similarities = linear_kernel(question_vector, self.tfidf_matrix).flatten()
        best_answer_indices = cosine_similarities.argsort()[-top_n:][::-1]
        return [(self.answers[i], cosine_similarities[i]) for i in best_answer_indices]
