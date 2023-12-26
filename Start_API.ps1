# デフォルトのブラウザでURLを開く
Start-Process "http://127.0.0.1:8001/docs"

# api.pyを実行
conda activate AI_Tuber
python .\api.py
Read-Host -Prompt "Press Enter to exit"
