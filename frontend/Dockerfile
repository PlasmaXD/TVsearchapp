# 例: Dockerfile
FROM python:3.9

# 必要なパッケージのインストール
COPY requirements.txt .
RUN pip install -r requirements.txt

# アプリのソースコードをコピー
COPY . /app
WORKDIR /app

# Cloud Run の PORT を使って Streamlit を起動
CMD streamlit run your_app.py --server.port=$PORT --server.enableCORS false
