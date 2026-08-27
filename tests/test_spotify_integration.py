import os
import unittest

from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

from spotify_service import SpotifyService


load_dotenv()


SCOPE = (
    "user-top-read "
    "playlist-read-private "
    "playlist-modify-private "
    "playlist-modify-public"
    "user-read-private "
)


@unittest.skipUnless(
    os.getenv("RUN_SPOTIFY_INTEGRATION_TESTS") == "1",
    "Spotify統合テストは通常は実行しません。"
)
class SpotifyIntegrationTest(unittest.TestCase):

    def setUp(self):
        spotify_oauth = SpotifyOAuth(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
            scope=SCOPE,
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