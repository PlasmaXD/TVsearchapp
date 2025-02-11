# recommendation.py
import pandas as pd
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split

from database import client  # Datastoreクライアント
# from scraper import get_program_details_from_scraper  # 必要ならスクレイピング用の関数を使う

def get_all_reviews():
    """
    全レビューを取得し、(user_id, program_id, rating) のタプルのリストとして返す。
    """
    query = client.query(kind='Review')
    results = list(query.fetch())
    all_reviews = []
    for r in results:
        user_id = r.get('user_id')
        program_id = r.get('program_id')
        rating = r.get('rating')
        if user_id and program_id and rating:
            all_reviews.append((user_id, program_id, float(rating)))
    return all_reviews

def get_popular_programs(n=10):
    """
    「人気番組」を返すための簡易実装。
    ここでは「レビュー数が多い番組」を上位N件取得する例。
    実装の仕方は自由に変更可能。
    """
    query = client.query(kind='Review')
    results = list(query.fetch())
    
    # program_id -> レビュー数, 最新のタイトル(上書きするだけ)
    count_dict = {}
    title_map = {}
    
    for r in results:
        pid = r.get('program_id')
        ptitle = r.get('program_title', 'No Title')
        if pid:
            count_dict[pid] = count_dict.get(pid, 0) + 1
            # 同じprogram_idでも最後に見つかったタイトルで更新しているだけ
            title_map[pid] = ptitle

    # レビュー数の多い順にソート
    sorted_programs = sorted(count_dict.items(), key=lambda x: x[1], reverse=True)
    top_program_ids = [pid for (pid, _) in sorted_programs[:n]]
    
    # 人気番組リストを作成
    popular_programs = []
    for pid in top_program_ids:
        popular_programs.append({
            'program_id': pid,
            'title': title_map.get(pid, f'Program {pid}'),
            # サンプルとして補足情報を適当に入れる
            'supplement': f"人気番組 (レビュー数: {count_dict[pid]})"
        })
    return popular_programs

def get_program_details_by_ids(program_ids):
    """
    取得した番組IDをもとに、番組の詳細情報をまとめて返す。
    - 本当は DBに番組情報を保存しておき、そこから取得するのが望ましい。
    - ここでは「タイトルやサプリメント情報が無い場合はダミーを入れる」例。
    - もしくはスクレイピング関数 get_program_details_from_scraper(pid) で補完することも可能。
    """
    details = []
    for pid in program_ids:
        # ここで DB or 別のAPI から詳細を取る処理が書ければベスト。
        # 例: detail = get_program_details_from_db(pid)
        #     if not detail: detail = get_program_details_from_scraper(pid)
        
        # 今はダミー実装: 見つからなかったらデフォルト値を挿入
        details.append({
            'program_id': pid,
            'title': f"Program {pid}",
            'supplement': f"Details of Program {pid}"
        })
    return details

def recommend_programs(user_id, n_recommendations=10):
    """
    1) ユーザーのレビューが少なければ人気番組を返す
    2) 一定以上あればSVDによる協調フィルタリングを行う
    """
    reviews = get_all_reviews()
    # ユーザーのレビューのみ抽出
    user_reviews = [r for r in reviews if r[0] == user_id]
    
    # コールドスタート対策: レビュー数が5件未満なら人気番組を返す
    if len(user_reviews) < 5:
        popular_programs = get_popular_programs(n_recommendations)
        return popular_programs

    # ========== 以下、SVDによるレコメンド ==========
    # Surprise 用に DataFrame を作成
    df = pd.DataFrame(reviews, columns=['user_id', 'program_id', 'rating'])
    reader = Reader(rating_scale=(1, 5))
    dataset = Dataset.load_from_df(df, reader)

    # 学習データとテストデータに分割（例: 75%学習 / 25%テスト）
    trainset, testset = train_test_split(dataset, test_size=0.25)

    # SVDモデルで学習
    algo = SVD()
    algo.fit(trainset)

    # ユーザーが既にレビューしている番組ID
    user_history = [item for (u, item, r) in reviews if u == user_id]
    # すべての番組ID (重複排除)
    all_programs = list(set([item for (_, item, _) in reviews]))
    # 未レビューの番組を抽出
    unseen_programs = [p for p in all_programs if p not in user_history]

    # 予測スコアの高い順にソートして上位N件を取得
    predictions = [algo.predict(user_id, p) for p in unseen_programs]
    predictions.sort(key=lambda x: x.est, reverse=True)
    top_n = predictions[:n_recommendations]
    recommended_ids = [pred.iid for pred in top_n]

    # 番組詳細の取得 (DB or スクレイピングなど)
    recommendations = get_program_details_by_ids(recommended_ids)
    return recommendations
