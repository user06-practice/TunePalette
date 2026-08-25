import os

from flask import Flask, redirect, request
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

from spotify_service import SpotifyService


# .env の内容を読み込む
load_dotenv()

app = Flask(__name__)


# Spotifyにどこまでの操作を許可してもらうか
SCOPE = (
    "user-top-read "
    "playlist-read-private "
    "playlist-modify-private "
    "playlist-modify-public"
)


# Spotify認証を担当するオブジェクト
spotify_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
    scope=SCOPE,
)

spotify_service = SpotifyService(spotify_oauth)


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

    spotify_oauth.get_access_token(code)

    return redirect("/playlists")

@app.route("/top")
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


if __name__ == "__main__":
    app.run(debug=True)