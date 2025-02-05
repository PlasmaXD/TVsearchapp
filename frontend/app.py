import streamlit as st
import requests
from google_auth_oauthlib.flow import Flow
import os
import json
import pathlib
from dotenv import load_dotenv
# .envファイルを読み込む
load_dotenv()

# 環境変数を取得
BACKEND_URL = os.getenv('BACKEND_URL')
# ===============================
# ここからGoogle OAuth関連の設定
# ===============================

CLIENT_SECRETS_FILE = str(pathlib.Path(__file__).parent / "client_secret.json")
# CLIENT_SECRETS_FILE = "/workspace/client_secret.json"

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]
REDIRECT_URI = os.getenv('REDIRECT_URI')

# "http://localhost:8501"  # ローカルならコレ, デプロイするならURLを合わせる

if "google_user" not in st.session_state:
    st.session_state.google_user = None  # Google アカウント情報 (email, name, etc.)
if "credentials" not in st.session_state:
    st.session_state.credentials = None  # OAuth2クレデンシャル(トークンなど)

def create_flow():
    """Google OAuthフローの初期化"""
    return Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

# ===============================
# ここからApp機能(検索、レビュー等)
# ===============================

if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "search_query" not in st.session_state:
    st.session_state.search_query = ""

def show_app_features():
    """
    ログイン済みユーザー向けに検索やレビュー投稿、お気に入り登録などのUIをまとめて表示する関数
    """
    st.header("番組検索＆レビュー投稿")

    # --- 検索UIと動作 ---
    search_query = st.text_input("番組の検索ワード", st.session_state.search_query)
    if st.button("検索"):
        st.session_state.search_query = search_query
        params = {"q": search_query}
        res = requests.get(f"{BACKEND_URL}/search", params=params)
        if res.status_code == 200:
            data = res.json()
            st.session_state.search_results = data.get("programs", [])
        else:
            st.error("検索に失敗しました。")
            st.session_state.search_results = []

    # --- 検索結果の表示とレビュー機能 ---
    for program in st.session_state.search_results:
        st.subheader(program["title"])
        st.write(program["supplement"])

        # 出演者の折りたたみ表示
        with st.expander("共演者を表示"):
            for cast_name in program.get("cast_names", []):
                st.write(f" - {cast_name}")

        # URL末尾から番組IDを推定する例（実際はバックエンドの返却値などにより調整）
        program_id = program["url"].split("/tv_events/")[-1]

        # レビュー投稿フォーム
        with st.form(key=f"review_form_{program_id}"):
            rating = st.slider("評価", 1, 5, 3)
            review_text = st.text_area("レビューを入力")
            submitted = st.form_submit_button("レビュー投稿")
            if submitted:
                payload = {
                    "program_id": program_id,
                    "program_title": program["title"],
                    "user_id": st.session_state.google_user.get("email"),  # GoogleアカウントのメールをユーザーID扱い例
                    "rating": rating,
                    "review_text": review_text
                }
                r = requests.post(f"{BACKEND_URL}/reviews", json=payload)
                if r.status_code in (200, 201):
                    st.success("レビューを投稿しました。")
                else:
                    st.error("レビュー投稿に失敗")

        # お気に入り登録
        if st.button(f"お気に入り登録: {program_id}"):
            fav_url = f"{BACKEND_URL}/favorites/{st.session_state.google_user.get('email')}/{program_id}"
            fav_res = requests.post(fav_url)
            if fav_res.status_code in (200, 201):
                st.success("お気に入りに追加しました。")
            else:
                st.error("お気に入り登録に失敗")

        # レビュー一覧の表示
        rev_res = requests.get(f"{BACKEND_URL}/reviews/program/{program_id}")
        if rev_res.status_code == 200:
            reviews_data = rev_res.json()  # List[Review]
            st.write("### レビュー一覧")
            if reviews_data:
                for rev in reviews_data:
                    st.markdown(f"""
                    **ユーザー**: {rev['user_id']}  
                    **評価**: {rev['rating']}  
                    **コメント**: {rev['review_text']}  
                    **投稿日**: {rev['created_at']}  
                    ---
                    """)
            else:
                st.write("まだレビューはありません。")
        else:
            st.error("レビュー取得に失敗")

        st.write("---")

    # ユーザーのお気に入り一覧を表示
    if st.button("自分のお気に入りを表示"):
        email = st.session_state.google_user.get("email")
        fav_res = requests.get(f"{BACKEND_URL}/favorites/" + email)
        if fav_res.status_code == 200:
            fav_data = fav_res.json()
            fav_programs = fav_data.get("favorite_programs", [])
            if fav_programs:
                st.write("お気に入り番組ID:", fav_programs)
            else:
                st.write("お気に入りはありません。")
        else:
            st.error("お気に入り取得に失敗")

    # レコメンド表示 (例)
    st.subheader("おすすめの番組")
    rec_res = requests.get(f"{BACKEND_URL}/recommendations/{st.session_state.google_user.get('email')}")
    if rec_res.status_code == 200:
        rec_data = rec_res.json()
        recommendations = rec_data.get("recommendations", [])
        if recommendations:
            for rec in recommendations:
                st.write(f" - {rec['title']}: {rec['supplement']}")
        else:
            st.write("おすすめ番組がありません")
    else:
        st.error("レコメンド取得に失敗")


# ===============================
# メインの描画フロー
# ===============================
st.title("番組検索＆レビュー投稿")

# --- すでにログイン済みの場合 ---
if st.session_state.google_user:
    st.success(f"ログイン中: {st.session_state.google_user.get('email')}")
    if st.button("ログアウト"):
        st.session_state.google_user = None
        st.session_state.credentials = None
        st.rerun()

    # ログイン済みなので検索やレビュー機能を表示
    show_app_features()

else:
    # 未ログイン時: ログインボタンとOAuthハンドリング
    st.info("Googleログインが必要です。")
    if st.button("Google でログイン"):
        # OAuth フロー開始
        flow = create_flow()
        auth_url, _ = flow.authorization_url(prompt="consent")
        st.write("以下のリンクを開いて認証してください:")
        st.write(auth_url)

    # 認可コードがURLに付いていれば取得
    query_params = st.experimental_get_query_params()
    if "code" in query_params:
        code = query_params["code"][0]
        flow = create_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials
        st.session_state.credentials = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes
        }

        # ユーザー情報を取得
        token_headers = {"Authorization": f"Bearer {credentials.token}"}
        user_info_res = requests.get("https://www.googleapis.com/oauth2/v2/userinfo", headers=token_headers)
        if user_info_res.status_code == 200:
            user_info = user_info_res.json()
            st.session_state.google_user = user_info
            st.rerun()
        else:
            st.error("ユーザー情報の取得に失敗しました。")
