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

    def test_search_real_tracks_by_artist(self):
        tracks = self.service.search_tracks_by_artist(
            "Simple Plan",
            limit=10
        )

        self.assertGreater(
            len(tracks),
            0
        )

        for track in tracks:
            self.assertTrue(track["id"])
            self.assertTrue(track["name"])
            self.assertTrue(track["artists"])
            self.assertTrue(track["uri"])
            self.assertIsNotNone(
                track["duration_ms"]
            )

    @unittest.skipUnless(
        os.getenv("RUN_SPOTIFY_WRITE_TESTS") == "1",
        "Spotify書き込み統合テストは通常は実行しません。"
    )
    def test_create_real_playlist_and_add_tracks(self):
        favorite_playlist_id = os.getenv(
            "SPOTIFY_FAVORITE_PLAYLIST_ID"
        )

        self.assertTrue(
            favorite_playlist_id,
            "SPOTIFY_FAVORITE_PLAYLIST_IDが設定されていません。"
        )

        favorite_tracks = self.service.get_playlist_tracks(
            favorite_playlist_id,
            limit=10
        )

        if len(favorite_tracks) < 2:
            self.skipTest(
                "FAVORITEにテスト用の曲が2曲以上ありません。"
            )

        test_tracks = favorite_tracks[:2]

        playlist = self.service.create_playlist(
            name="TunePalette Integration Test",
            public=False,
            description="TunePalette Spotify API write test"
        )

        self.assertTrue(playlist["id"])

        self.service.add_tracks_to_playlist(
            playlist["id"],
            test_tracks
        )

        saved_tracks = self.service.get_playlist_tracks(
            playlist["id"],
            limit=10
        )

        self.assertEqual(
            len(saved_tracks),
            2
        )

        self.assertEqual(
            saved_tracks[0]["id"],
            test_tracks[0]["id"]
        )

        self.assertEqual(
            saved_tracks[1]["id"],
            test_tracks[1]["id"]
        )