import os

from flask import Flask, redirect, request, session, abort, url_for
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from spotify_service import SpotifyService
from spotipy.cache_handler import MemoryCacheHandler
from functools import wraps


# .env の内容を読み込む
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")


# Spotifyにどこまでの操作を許可してもらうか
SCOPE = (
    "user-top-read "
    "user-read-private "
    "playlist-read-private "
    "playlist-modify-private "
    "playlist-modify-public"
)


# Spotify認証を担当するオブジェクト
spotify_token_cache = MemoryCacheHandler()

spotify_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
    scope=SCOPE,
    cache_handler=spotify_token_cache,
)

spotify_service = SpotifyService(spotify_oauth)

def login_required(view_function):
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):

        # このブラウザで本人確認が済んでいない
        if not session.get("authorized", False):
            return redirect(url_for("login"))

        # サーバー再起動などでSpotify Tokenが消えている
        token_info = spotify_token_cache.get_cached_token()

        if not token_info:
            session.clear()
            return redirect(url_for("login"))

        return view_function(*args, **kwargs)

    return wrapped_view

@app.route("/")
def index():
    return '<a href="/login">Spotifyでログイン</a>'


@app.route("/login")
def login():
    auth_url = spotify_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route("/callback")
def callback():
    code = request.args.get("code")

    if not code:
        return "Spotify認証に失敗しました。"

    # 本人確認が終わるまでは正式なキャッシュへ保存しない
    temporary_cache = MemoryCacheHandler()

    temporary_oauth = SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
        scope=SCOPE,
        cache_handler=temporary_cache,
    )

    # Spotifyから一時的なTokenを取得
    temporary_oauth.get_access_token(code, as_dict=False)

    # MemoryCacheHandlerからToken情報を取得
    token_info = temporary_cache.get_cached_token()

    # 一時Tokenを使って、Spotifyユーザー本人を確認
    temporary_service = SpotifyService(temporary_oauth)
    account = temporary_service.get_current_account()

    allowed_account_id = os.getenv("SPOTIFY_ALLOWED_ACCOUNT_ID")

    # 自分以外なら拒否
    if account["account_id"] != allowed_account_id:
        session.clear()
        abort(403)

    # 本人だった場合だけ正式なメモリキャッシュへTokenを保存
    spotify_token_cache.save_token_to_cache(token_info)

    # このブラウザを「本人確認済み」として記録
    session["authorized"] = True

    return redirect(url_for("playlists"))

@app.route("/top")
@login_required
def top_tracks():
    tracks = spotify_service.get_top_tracks(
        limit=10,
        time_range="medium_term"
    )

    output = "<h1>よく聴いている曲</h1>"

    for track in tracks:
        track_name = track["name"]
        artist_name = ", ".join(track["artists"])

        output += f"<p>{artist_name} - {track_name}</p>"

    return output

@app.route("/playlists")
@login_required
def playlists():
    playlists = spotify_service.get_playlists(limit=50)

    output = "<h1>Spotifyのプレイリスト</h1>"

    for playlist in playlists:
        playlist_name = playlist["name"]
        playlist_id = playlist["id"]

        output += (
            f'<p>'
            f'<a href="/playlist/{playlist_id}">'
            f'{playlist_name}'
            f'</a>'
            f'</p>'
        )

    return output

@app.route("/playlist/<playlist_id>")
@login_required
def playlist_detail(playlist_id):
    tracks = spotify_service.get_playlist_tracks(
        playlist_id,
        limit=50
    )

    output = "<h1>プレイリストの曲</h1>"

    for track in tracks:
        track_name = track["name"]
        artist_name = ", ".join(track["artists"])

        output += f"<p>{artist_name} - {track_name}</p>"

    output += '<p><a href="/playlists">プレイリスト一覧へ戻る</a></p>'

    return output

@app.route("/whoami")
@login_required
def whoami():
    account = spotify_service.get_current_account()

    return (
        "<h1>Spotifyアカウント確認</h1>"
        f"<p>表示名: {account['display_name']}</p>"
        f"<p>account_id: {account['account_id']}</p>"
    )



if __name__ == "__main__":
    app.run(debug=True)