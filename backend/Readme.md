### 実行方法
```bash
cd backend
pip install -r requirements.txt
```
### 実行方法
```bash
uvicorn main:app --reload
```

Docker イメージをビルド
```bash
docker build -t tvapp-backend .
```

Docker コンテナを起動


```bash
docker run -d -p 8000:8000 tvapp-backend
```
http://localhost:8000/search?q=あ
