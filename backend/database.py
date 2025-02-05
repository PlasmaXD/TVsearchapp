# database.py
from google.cloud import datastore
from typing import List
from datetime import datetime
import uuid
import os

print("DATASTORE_EMULATOR_HOST:", os.getenv("DATASTORE_EMULATOR_HOST"))
print("DATASTORE_PROJECT_ID:", os.getenv("DATASTORE_PROJECT_ID"))

# Datastore クライアントの初期化
client = datastore.Client()

# -------------------
# ユーザー関連
# -------------------
def add_user(user_id: str, user_name: str):
    """
    Datastore の Users Kind にユーザーを追加
    """
    key = client.key('User', user_id)
    entity = datastore.Entity(key=key)
    entity.update({
        'user_name': user_name
    })
    client.put(entity)

def get_user(user_id: str):
    """
    userId で Users Kind を取得
    """
    key = client.key('User', user_id)
    entity = client.get(key)
    if entity:
        return (entity.key.name, entity.get('user_name'))
    else:
        return None

# -------------------
# レビュー関連
# -------------------
def add_review(program_id: str, program_title: str, user_id: str, rating: int, review_text: str):
    """
    Datastore の Reviews Kind にレビューを追加
    review_id は UUID を使用
    """
    review_id = str(uuid.uuid4())
    created_at = datetime.utcnow()

    key = client.key('Review', review_id)
    entity = datastore.Entity(key=key)
    entity.update({
        'review_id': review_id,  # review_id をフィールドとして保存
        'program_id': program_id,
        'program_title': program_title,
        'user_id': user_id,
        'rating': rating,
        'review_text': review_text,
        'created_at': created_at
    })
    client.put(entity)

def get_reviews_by_program(program_id: str) -> List[dict]:
    """
    programId で Reviews Kind をクエリ
    """
    query = client.query(kind='Review')
    query.add_filter('program_id', '=', program_id)
    query.order = ['-created_at']  # 新しい順
    results = list(query.fetch())
    return results

# -------------------
# お気に入り関連
# -------------------
def add_favorite(user_id: str, program_id: str):
    """
    Datastore の Favorites Kind にお気に入りを追加
    user_id を親キーとして program_id を子キーとして設定
    """
    # パスの設定: User > Favorite
    parent_key = client.key('User', user_id)
    key = client.key('Favorite', program_id, parent=parent_key)
    entity = datastore.Entity(key=key)
    entity.update({
        'program_id': program_id
    })
    client.put(entity)

def get_favorites(user_id: str) -> List[str]:
    """
    userId で Favorites Kind をクエリし、program_id の一覧を返す
    """
    parent_key = client.key('User', user_id)
    query = client.query(kind='Favorite', ancestor=parent_key)
    query.keys_only()
    results = list(query.fetch())
    program_ids = [entity.key.name for entity in results]
    return program_ids
