# main.py
from fastapi import FastAPI, Query, HTTPException, Depends, Request
from typing import List
from scraper import get_program_details  # スクレイピングロジックがある場合
from database import (
    add_user, get_user,
    add_review, get_reviews_by_program,
    add_favorite, get_favorites
)
from models import UserCreate, User, ReviewCreate, Review
from recommendation import recommend_programs

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello, this is backend API!"}

@app.get("/search")
def search_programs(q: str = Query(None)):
    """
    検索クエリ q を受け取ってスクレイピングし、結果を返す。
    例: GET /search?q=ドラマ
    """
    if not q:
        raise HTTPException(status_code=400, detail="No query provided.")
    data = get_program_details(q)
    return {"programs": data}

# ----- ユーザー関連 -----
@app.post("/users", response_model=User, status_code=201)
def create_user(user: UserCreate):
    """
    新規ユーザー登録
    """
    # すでに存在するかチェック
    existing_user = get_user(user.user_id)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists.")
    
    # DBに追加
    add_user(user.user_id, user.user_name)
    # DBから取り直して返す
    db_user = get_user(user.user_id)
    if db_user:
        return User(user_id=db_user[0], user_name=db_user[1])
    else:
        raise HTTPException(status_code=500, detail="Could not create user.")

@app.get("/users/{user_id}", response_model=User)
def get_user_by_id(user_id: str):
    """
    ユーザーID指定で取得
    """
    db_user = get_user(user_id)
    if db_user:
        return User(user_id=db_user[0], user_name=db_user[1])
    else:
        raise HTTPException(status_code=404, detail="User not found.")

# ----- レビュー関連 -----
@app.post("/reviews", status_code=201)
def create_review(review: ReviewCreate):
    """
    新規レビュー投稿
    """
    add_review(
        program_id=review.program_id,
        program_title=review.program_title,
        user_id=review.user_id,
        rating=review.rating,
        review_text=review.review_text
    )
    return {"message": "Review added successfully"}

@app.get("/reviews/program/{program_id}", response_model=List[Review])
def get_reviews_for_program(program_id: str):
    """
    ある番組IDに対するレビュー一覧を取得
    """
    rows = get_reviews_by_program(program_id)
    results = []
    for row in rows:
        try:
            results.append(Review(
                review_id=row["review_id"],  # 'review_id' に修正
                program_id=row["program_id"],
                program_title=row["program_title"],
                user_id=row["user_id"],
                rating=row["rating"],
                review_text=row["review_text"],
                created_at=row["created_at"]
            ))
        except KeyError as e:
            # ログにエラーを記録し、詳細を確認できるようにする
            print(f"KeyError: {e} in row: {row}")
            raise HTTPException(status_code=500, detail=f"Missing field: {e}")
    return results

# ----- お気に入り関連 -----
@app.post("/favorites/{user_id}/{program_id}")
def create_favorite(user_id: str, program_id: str):
    """
    お気に入り登録
    """
    add_favorite(user_id, program_id)
    return {"message": "Favorite added"}

@app.get("/favorites/{user_id}")
def get_favorite_list(user_id: str):
    """
    ユーザーのお気に入り一覧を取得
    """
    programs = get_favorites(user_id)
    return {"user_id": user_id, "favorite_programs": programs}


@app.get("/recommendations/{user_id}")
def get_recommendations(user_id: str, n: int = 10):
    """
    ユーザーIDと推薦件数を指定して番組推薦を受け取るエンドポイント
    """
    recommended = recommend_programs(user_id, n_recommendations=n)
    return {"recommendations": recommended}