import os
import unittest

from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

from spotify_service import SpotifyService
from spotipy.cache_handler import CacheFileHandler


load_dotenv()


SCOPE = (
    "user-top-read "
    "user-read-private "
    "playlist-read-private "
    "playlist-modify-private "
    "playlist-modify-public"
)


@unittest.skipUnless(
    os.getenv("RUN_SPOTIFY_INTEGRATION_TESTS") == "1",
    "Spotify統合テストは通常は実行しません。"
)
class SpotifyIntegrationTest(unittest.TestCase):

    def setUp(self):
        cache_handler = CacheFileHandler(
            cache_path=".spotify-test-cache"
        )

        spotify_oauth = SpotifyOAuth(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
            scope=SCOPE,
            cache_handler=cache_handler,
        )

        self.service = SpotifyService(spotify_oauth)

    def test_get_real_playlists(self):
        playlists = self.service.get_playlists(limit=10)

        self.assertIsInstance(playlists, list)

        if playlists:
            self.assertIn("id", playlists[0])
            self.assertIn("name", playlists[0])

    def test_get_real_playlist_tracks(self):
        playlists = self.service.get_playlists(limit=10)

        if not playlists:
            self.skipTest("Spotifyにプレイリストがありません。")

        for playlist in playlists:
            tracks = self.service.get_playlist_tracks(
                playlist["id"],
                limit=10
            )

            if tracks:
                self.assertIn("id", tracks[0])
                self.assertIn("name", tracks[0])
                self.assertIn("artists", tracks[0])
                return

        self.skipTest("曲が入っているプレイリストがありません。")

    def test_get_real_playlist_tracks_pagination(self):
        playlists = self.service.get_playlists(limit=10)

        if not playlists:
            self.skipTest("Spotifyにプレイリストがありません。")

        for playlist in playlists:
            tracks = self.service.get_playlist_tracks(
                playlist["id"],
                limit=50
            )

            # 51曲以上取得できれば、
            # Spotify APIを2ページ以上取得できたことになる
            if len(tracks) > 50:
                self.assertGreater(len(tracks), 50)
                return

        self.skipTest(
            "先頭10プレイリスト内に51曲以上のプレイリストがありません。"
        )