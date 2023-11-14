import os
import csv
import pandas as pd
from joblib import dump, load
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from janome.tokenizer import Tokenizer

from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
import pprint

class AnswerFinder:
    def __init__(self):
        self.csv_list = None
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.tokenizer = Tokenizer()
        self.remove_words = ['、', '。', ' ','　','…']

    def create_or_load_chroma_db(self, csv_directory, persist_directory):
        if self._is_new_csv_exists(csv_directory) or self.is_directory_empty(persist_directory):
            #新規DBの作成
            csv_loader = DirectoryLoader(path=csv_directory,
                                        glob="**/*.csv",
                                        show_progress=False)
            text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
                separator = "\n\n",  # セパレータ
                chunk_size=100,  # チャンクのトークン数
                chunk_overlap=0  # チャンクオーバーラップのトークン数
            )
            documents = csv_loader.load_and_split(text_splitter=text_splitter)
            db = Chroma.from_documents(documents,
                                    OpenAIEmbeddings(),
                                    persist_directory = persist_directory)
            return db
        else:
            # load from disk
            db = Chroma(persist_directory=persist_directory, embedding_function=OpenAIEmbeddings())
            return db
        
    def create_or_load_tf_idf_model(self, csv_directory, vetor_model_path):
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
            self.load_tfidf_model(vetor_model_path)
    
    def load_tfidf_model(self, vetor_model_path):
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

    def save_tfidf_to_csv(self,csv_file_path):
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
        directory以下のCSVファイルをソートし、CSVをTokenごとに出力
        """
        csv_files = [os.path.join(root, filename)
                     for root, dirs, files in os.walk(directory)
                     for filename in files if filename.endswith('.csv')]
        answers = []
        for csv_file in csv_files:
            df = pd.read_csv(csv_file, skiprows=1)  # 最初の行をスキップ
            answers.extend(df.iloc[:, 0].tolist())
        return answers
    
    def is_directory_empty(self,directory):
        # ディレクトリの総サイズを計算する
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for f in filenames:
                # ファイルのパスを取得
                fp = os.path.join(dirpath, f)
                # ファイルが実際に存在するかを確認（シンボリックリンクの場合など）
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)

        # ディレクトリのサイズが0の場合にTrueを返す
        return total_size == 0
    
    def find_similar_tfidf(self, question, top_n=3):
        question_vector = self.tfidf_vectorizer.transform([question])
        cosine_similarities = linear_kernel(question_vector, self.tfidf_matrix).flatten()
        best_answer_indices = cosine_similarities.argsort()[-top_n:][::-1]
        return [{'text': self.csv_list[i], 'score': cosine_similarities[i]} for i in best_answer_indices]
    
    def remove_duplicates(self,dict_list):
        """
        辞書のリストから、'text'キーの値が重複する辞書を除去する。

        :param dict_list: 辞書のリスト
        :return: 重複の除去されたリスト
        """
        seen_texts = set()
        new_list = []

        for item in dict_list:
            if item['text'] not in seen_texts:
                new_list.append(item)
                seen_texts.add(item['text'])

        return new_list

    def find_similar_vector_store(self, db,question, top_n=3):
        #探索モードはsimilarity search
        #retriver = self.db.as_retriever(search_kwargs={"k": top_n})
        #return retriver.get_relevant_documents(question)
        raw_result =  db.similarity_search_with_score(query=question, k=top_n)
        result = [{'text': doc.page_content, 'score': score} for doc, score in raw_result]
        return self.remove_duplicates(result)
    
    def tokenize(self, text):
        return [token.surface for token in self.tokenizer.tokenize(text)]

if __name__ == '__main__':
    finder = AnswerFinder()
    pp = pprint.PrettyPrinter(indent=2)
    tone_db=finder.create_or_load_chroma_db(csv_directory='memory/example_tone', persist_directory='memory/ChromaDB')
    finder.create_or_load_tf_idf_model(csv_directory='memory/example_tone', vetor_model_path='memory/tf-idf_model.pkl')
    while True:
        print("endにて終了")
        serch_word = input("検索ワードを入力してください:")
        if serch_word == 'end':
            break
        results = finder.find_similar_vector_store(tone_db,serch_word,3)
        print('[Vector Store]')
        pp.pprint(results)
        results = finder.find_similar_tfidf(serch_word,3)
        print('\n[tf_idf]')
        pp.pprint(results)
        
    #csv_output_path = 'memory/tfidf_vectors.csv'
    #finder.save_tfidf_to_csv(csv_output_path)