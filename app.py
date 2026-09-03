import os

from flask import (
    Flask,
    redirect,
    request,
    session,
    abort,
    url_for,
    render_template,
)
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from spotify_service import SpotifyService
from spotipy.cache_handler import MemoryCacheHandler
from functools import wraps
from music_library import MusicLibrary
from playlist_generator import PlaylistGenerator
from lastfm_service import LastfmService
from discovery_service import DiscoveryService
from mood_service import MoodService



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

music_library = MusicLibrary(
    spotify_service,
    os.getenv("SPOTIFY_FAVORITE_PLAYLIST_ID")
)

lastfm_service = LastfmService(
    os.getenv("LASTFM_API_KEY")
)

mood_service = MoodService(
    lastfm_service
)

discovery_service = DiscoveryService(
    music_library,
    lastfm_service,
    spotify_service
)

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

    return redirect(
        url_for("settings")
    )

@app.route("/settings")
@login_required
def settings():
    return render_template(
        "settings.html"
    )

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

@app.route("/favorites")
@login_required
def favorites():
    tracks = music_library.get_favorite_tracks()

    output = f"<h1>FAVORITE ({len(tracks)}曲)</h1>"

    for track in tracks:
        track_name = track["name"]
        artist_name = ", ".join(track["artists"])

        duration_ms = track["duration_ms"]
        release_year = track["release_year"]

        if duration_ms is not None:
            total_seconds = duration_ms // 1000
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            duration_text = f"{minutes}:{seconds:02d}"
        else:
            duration_text = "不明"

        if release_year is not None:
            year_text = f"{release_year}年"
        else:
            year_text = "年代不明"

        output += (
            f"<p>"
            f"{artist_name} - {track_name}"
            f" - {duration_text}"
            f" - {year_text}"
            f"</p>"
        )

    return output

@app.route("/favorite-preview")
@login_required
def favorite_preview():
    tracks = music_library.get_favorite_tracks()

    analyzed_tracks = [
        mood_service.analyze_track(track)
        for track in tracks
    ]

    targets = PlaylistGenerator.get_source_time_targets(
        total_minutes=60,
        discovery_ratio=40
    )

    selected_tracks = PlaylistGenerator.select_favorite_tracks(
        tracks=analyzed_tracks,
        target_ms=targets["favorite_ms"],
        recency=50,
        mood=50
    )

    total_ms = sum(
        track["duration_ms"]
        for track in selected_tracks
    )

    total_seconds = total_ms // 1000
    total_minutes = total_seconds // 60
    remaining_seconds = total_seconds % 60

    output = (
        "<h1>FAVORITE 選曲プレビュー</h1>"
        "<p>設定: 60分 / 知らない曲40% / recency 50</p>"
        "<p>FAVORITE目標: 36:00</p>"
        f"<p>実際: {total_minutes}:{remaining_seconds:02d}</p>"
        f"<p>曲数: {len(selected_tracks)}曲</p>"
    )

    for track in selected_tracks:
        duration_ms = track["duration_ms"]
        seconds = duration_ms // 1000

        duration_text = (
            f"{seconds // 60}:{seconds % 60:02d}"
        )

        artist_name = ", ".join(track["artists"])

        mood_score = track.get("mood_score")

        if mood_score is None:
            mood_text = "判定不可"
        else:
            mood_text = f"{mood_score:.1f}"

        output += (
            f"<p>"
            f"{artist_name} - {track['name']}"
            f" - {duration_text}"
            f" - {track['release_year']}年"
            f" - mood: {mood_text}"
            f"</p>"
        )

    return output

@app.route("/lastfm-similar")
@login_required
def lastfm_similar():
    artists = lastfm_service.get_similar_artists(
        "Sum 41",
        limit=10
    )

    output = "<h1>Sum 41 に似ているアーティスト</h1>"

    for artist in artists:
        name = artist["name"]
        similarity = artist["similarity"]

        output += (
            f"<p>"
            f"{name} - 類似度 {similarity:.3f}"
            f"</p>"
        )

    return output

@app.route("/discovery-artists")
@login_required
def discovery_artists():
    candidates = discovery_service.get_candidate_artists(
        seed_limit=5,
        similar_limit=10
    )

    output = (
        "<h1>DISCOVERED候補アーティスト</h1>"
        f"<p>候補数: {len(candidates)}組</p>"
    )

    candidates = sorted(
        candidates,
        key=lambda artist: artist["similarity"],
        reverse=True
    )

    for artist in candidates:
        source_text = ", ".join(
            artist["source_artists"]
        )

        output += (
            f"<p>"
            f"<strong>{artist['name']}</strong>"
            f" - 類似度 {artist['similarity']:.3f}"
            f" - 起点: {source_text}"
            f"</p>"
        )

    return output

@app.route("/discovery-tracks")
@login_required
def discovery_tracks():
    candidate_artists = (
        discovery_service.get_candidate_artists(
            seed_limit=5,
            similar_limit=10
        )
    )

    candidate_tracks = (
        discovery_service.get_candidate_tracks(
            candidate_artists,
            artist_limit=10,
            tracks_per_artist=10
        )
    )

    output = (
        "<h1>DISCOVERED候補曲</h1>"
        f"<p>候補アーティスト数: {len(candidate_artists)}組</p>"
        f"<p>候補曲数: {len(candidate_tracks)}曲</p>"
    )

    for track in candidate_tracks:
        artist_name = ", ".join(
            track["artists"]
        )

        source_text = ", ".join(
            track["source_artists"]
        )

        release_year = track["release_year"]

        if release_year is None:
            year_text = "年代不明"
        else:
            year_text = f"{release_year}年"

        output += (
            f"<p>"
            f"<strong>{artist_name} - {track['name']}</strong>"
            f" - {year_text}"
            f" - 類似度 {track['similarity']:.3f}"
            f" - 起点: {source_text}"
            f"</p>"
        )

    return output

@app.route("/discovery-preview")
@login_required
def discovery_preview():
    candidate_artists = (
        discovery_service.get_candidate_artists(
            seed_limit=5,
            similar_limit=10
        )
    )

    candidate_tracks = (
        discovery_service.get_candidate_tracks(
            candidate_artists,
            artist_limit=10,
            tracks_per_artist=10
        )
    )

    # DISCOVERED候補曲に
    # アーティスト単位のmood_scoreを付与
    analyzed_tracks = (
        mood_service.analyze_discovered_tracks(
            candidate_tracks
        )
    )

    targets = PlaylistGenerator.get_source_time_targets(
        total_minutes=60,
        discovery_ratio=40
    )

    selected_tracks = (
        PlaylistGenerator.select_discovered_tracks(
            tracks=analyzed_tracks,
            target_ms=targets["discovered_ms"],
            recency=50,
            mood=50
        )
    )

    total_ms = sum(
        track["duration_ms"]
        for track in selected_tracks
    )

    total_seconds = total_ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60

    output = (
        "<h1>DISCOVERED 選曲プレビュー</h1>"
        "<p>設定: 60分 / 知らない曲40% / recency 50</p>"
        "<p>DISCOVERED目標: 24:00</p>"
        f"<p>実際: {minutes}:{seconds:02d}</p>"
        f"<p>候補曲数: {len(candidate_tracks)}曲</p>"
        f"<p>選曲数: {len(selected_tracks)}曲</p>"
    )

    for track in selected_tracks:
        duration_seconds = track["duration_ms"] // 1000
        duration_text = (
            f"{duration_seconds // 60}:"
            f"{duration_seconds % 60:02d}"
        )

        artist_name = ", ".join(
            track["artists"]
        )

        mood_score = track.get("mood_score")

        if mood_score is None:
            mood_text = "判定不可"
        else:
            mood_text = f"{mood_score:.1f}"

        mood_tags = track.get(
            "mood_tags",
            []
        )

        tags_text = ", ".join(
            mood_tags
        )

        discovery_artist = track.get(
            "discovery_artist",
            "不明"
        )

        output += (
            f"<p>"
            f"<strong>{artist_name} - {track['name']}</strong>"
            f"<br>"
            f"再生時間: {duration_text}"
            f" / 年代: {track['release_year']}年"
            f" / mood: {mood_text}"
            f"<br>"
            f"判定アーティスト: {discovery_artist}"
            f"<br>"
            f"Last.fm tags: {tags_text}"
            f"</p>"
            f"<hr>"
        )

    return output

@app.route("/create-playlist", methods=["POST"])
@login_required
def create_playlist():

    # -------------------------
    # 設定画面から値を受け取る
    # -------------------------

    mood = request.form.get(
        "mood",
        default=50,
        type=int
    )

    discovery_ratio = request.form.get(
        "discovery_ratio",
        default=40,
        type=int
    )

    recency = request.form.get(
        "recency",
        default=50,
        type=int
    )

    duration = request.form.get(
        "duration",
        default=60,
        type=int
    )


    # -------------------------
    # 入力値チェック
    # -------------------------

    if not 0 <= mood <= 100:
        abort(400)

    if not 0 <= discovery_ratio <= 100:
        abort(400)

    if not 0 <= recency <= 100:
        abort(400)

    if duration not in {
        30,
        60,
        90,
        120,
    }:
        abort(400)


    # -------------------------
    # FAVORITE / DISCOVERED
    # の目標時間を計算
    # -------------------------

    targets = (
        PlaylistGenerator.get_source_time_targets(
            total_minutes=duration,
            discovery_ratio=discovery_ratio
        )
    )


    # -------------------------
    # FAVORITEを選曲
    # -------------------------

    favorite_tracks = []

    if targets["favorite_ms"] > 0:

        favorite_candidates = (
            music_library.get_favorite_tracks()
        )

        favorite_candidates = [
            mood_service.analyze_track(track)
            for track in favorite_candidates
        ]

        favorite_tracks = (
            PlaylistGenerator.select_favorite_tracks(
                tracks=favorite_candidates,
                target_ms=targets["favorite_ms"],
                recency=recency,
                mood=mood
            )
        )


    # -------------------------
    # DISCOVEREDを選曲
    # -------------------------

    discovered_tracks = []

    if targets["discovered_ms"] > 0:

        candidate_artists = (
            discovery_service.get_candidate_artists(
                seed_limit=5,
                similar_limit=10
            )
        )

        discovered_candidates = (
            discovery_service.get_candidate_tracks(
                candidate_artists,
                artist_limit=10,
                tracks_per_artist=10
            )
        )

        discovered_candidates = (
            mood_service.analyze_discovered_tracks(
                discovered_candidates
            )
        )

        discovered_tracks = (
            PlaylistGenerator.select_discovered_tracks(
                tracks=discovered_candidates,
                target_ms=targets["discovered_ms"],
                recency=recency,
                mood=mood
            )
        )


    # -------------------------
    # 2種類を混ぜる
    # -------------------------

    mixed_tracks = (
        PlaylistGenerator.mix_tracks(
            favorite_tracks,
            discovered_tracks
        )
    )

    if not mixed_tracks:
        return (
            "選曲できる曲がありませんでした。"
            '<br><a href="/settings">設定画面へ戻る</a>',
            500
        )

    # -------------------------
    # TunePaletteを取得
    # -------------------------

    playlist_name = "TunePalette"

    playlist = (
        spotify_service.find_playlist_by_name(
            playlist_name
        )
    )

    # -------------------------
    # 初回だけ新規作成
    # -------------------------

    if playlist is None:

        playlist = spotify_service.create_playlist(
            name=playlist_name,
            public=False,
            description=(
                "TunePaletteで自動生成した"
                "プレイリスト"
            )
        )

        spotify_service.add_tracks_to_playlist(
            playlist_id=playlist["id"],
            tracks=mixed_tracks
        )


    # -------------------------
    # 2回目以降は全曲置換
    # -------------------------

    else:

        spotify_service.replace_playlist_tracks(
            playlist_id=playlist["id"],
            tracks=mixed_tracks
        )


    # POSTの結果を直接表示せず、
    # GETの完了画面へ移動する
    return redirect(
        url_for(
            "playlist_created",
            playlist_id=playlist["id"]
        )
    )


@app.route("/playlist-created/<playlist_id>")
@login_required
def playlist_created(playlist_id):

    spotify_url = (
        f"https://open.spotify.com/playlist/"
        f"{playlist_id}"
    )

    return (
        "<h1>TunePaletteを更新しました！</h1>"
        "<p>新しい選曲がSpotifyに反映されました。</p>"
        f'<p>'
        f'<a href="{spotify_url}" target="_blank">'
        f'Spotifyで開く'
        f'</a>'
        f'</p>'
        '<p>'
        '<a href="/settings">'
        'もう一度作る'
        '</a>'
        '</p>'
    )

@app.route("/playlist-preview")
@login_required
def playlist_preview():
    mood = request.args.get(
        "mood",
        default=50,
        type=int
    )

    discovery_ratio = request.args.get(
        "discovery_ratio",
        default=40,
        type=int
    )

    recency = request.args.get(
        "recency",
        default=50,
        type=int
    )

    duration = request.args.get(
        "duration",
        default=60,
        type=int
    )

    # URLを直接書き換えられた場合にも備えて確認
    if not 0 <= mood <= 100:
        abort(400)

    if not 0 <= discovery_ratio <= 100:
        abort(400)

    if not 0 <= recency <= 100:
        abort(400)

    if duration not in {
        30,
        60,
        90,
        120,
    }:
        abort(400)

    # FAVORITEを取得
    favorite_candidates = (
        music_library.get_favorite_tracks()
    )

    favorite_candidates = [
        mood_service.analyze_track(track)
        for track in favorite_candidates
    ]

    # DISCOVERED候補アーティストを取得
    candidate_artists = (
        discovery_service.get_candidate_artists(
            seed_limit=5,
            similar_limit=10
        )
    )

    # DISCOVERED候補曲を取得
    discovered_candidates = (
        discovery_service.get_candidate_tracks(
            candidate_artists,
            artist_limit=10,
            tracks_per_artist=10
        )
    )

    discovered_candidates = (
        mood_service.analyze_discovered_tracks(
            discovered_candidates
        )
    )

    # 60分・知らない曲40%の時間配分
    targets = PlaylistGenerator.get_source_time_targets(
        total_minutes=duration,
        discovery_ratio=discovery_ratio
    )

    # FAVORITEを約36分選曲
    favorite_tracks = (
        PlaylistGenerator.select_favorite_tracks(
            tracks=favorite_candidates,
            target_ms=targets["favorite_ms"],
            recency=recency,
            mood=mood
        )
    )

    # DISCOVEREDを約24分選曲
    discovered_tracks = (
        PlaylistGenerator.select_discovered_tracks(
            tracks=discovered_candidates,
            target_ms=targets["discovered_ms"],
            recency=recency,
            mood=mood
        )
    )

    # 2種類を混ぜる
    mixed_tracks = PlaylistGenerator.mix_tracks(
        favorite_tracks,
        discovered_tracks
    )

    # 実際の時間を計算
    favorite_ms = sum(
        track["duration_ms"]
        for track in favorite_tracks
    )

    discovered_ms = sum(
        track["duration_ms"]
        for track in discovered_tracks
    )

    total_ms = favorite_ms + discovered_ms

    def format_duration(duration_ms):
        total_seconds = duration_ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60

        return f"{minutes}:{seconds:02d}"

    output = (
        "<h1>TunePalette プレイリストプレビュー</h1>"
        f"<p>"
        f"設定: {duration}分"
        f" / 知らない曲 {discovery_ratio}%"
        f" / recency {recency}"
        f" / mood {mood}"
        f"</p>"
        f"<p>FAVORITE: "
        f"{format_duration(favorite_ms)} "
        f"({len(favorite_tracks)}曲)</p>"
        f"<p>DISCOVERED: "
        f"{format_duration(discovered_ms)} "
        f"({len(discovered_tracks)}曲)</p>"
        f"<p><strong>合計: "
        f"{format_duration(total_ms)} "
        f"({len(mixed_tracks)}曲)</strong></p>"
        "<hr>"
    )

    for track in mixed_tracks:
        artist_name = ", ".join(
            track["artists"]
        )

        duration_text = format_duration(
            track["duration_ms"]
        )

        release_year = track["release_year"]

        if release_year is None:
            year_text = "年代不明"
        else:
            year_text = f"{release_year}年"

        output += (
            f"<p>"
            f"[{track['source']}] "
            f"<strong>{artist_name} - {track['name']}</strong>"
            f" - {duration_text}"
            f" - {year_text}"
            f"</p>"
        )

    return output

@app.route("/mood-preview")
@login_required
def mood_preview():
    tracks = music_library.get_favorite_tracks()

    # 今回は確認用に先頭5曲だけ
    sample_tracks = tracks[:5]

    output = "<h1>FAVORITE mood_score確認</h1>"

    for track in sample_tracks:
        analyzed = mood_service.analyze_track(track)

        artist_name = ", ".join(
            analyzed["artists"]
        )

        mood_score = analyzed["mood_score"]

        if mood_score is None:
            score_text = "判定不可"
        else:
            score_text = f"{mood_score:.1f}"

        tags_text = ", ".join(
            analyzed["mood_tags"]
        )

        output += (
            f"<h3>{artist_name} - {analyzed['name']}</h3>"
            f"<p>mood_score: {score_text}</p>"
            f"<p>mood_tag_source: {analyzed['mood_tag_source']}</p>"
            f"<p>Last.fm tags: {tags_text}</p>"
            f"<hr>"
        )

    return output

if __name__ == "__main__":
    app.run(debug=True)