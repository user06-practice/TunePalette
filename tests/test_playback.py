import os
import unittest
from unittest.mock import patch

from spotipy.exceptions import SpotifyException


# app.pyをimportする前に
# テスト用環境変数を設定
os.environ.setdefault(
    "FLASK_SECRET_KEY",
    "test-secret-key"
)

os.environ.setdefault(
    "SPOTIFY_CLIENT_ID",
    "test-client-id"
)

os.environ.setdefault(
    "SPOTIFY_CLIENT_SECRET",
    "test-client-secret"
)

os.environ.setdefault(
    "SPOTIFY_REDIRECT_URI",
    "http://127.0.0.1:5000/callback"
)

os.environ.setdefault(
    "SPOTIFY_ALLOWED_ACCOUNT_ID",
    "allowed-account"
)


import app as app_module


class PlaybackRouteTest(unittest.TestCase):

    def setUp(self):
        app_module.app.config["TESTING"] = True
        app_module.app.config[
            "SECRET_KEY"
        ] = "test-secret-key"

        self.client = (
            app_module.app.test_client()
        )

        # Play Playlistルートは
        # login_required付きなので、
        # 本人確認済みにしておく
        with self.client.session_transaction() as session:
            session["authorized"] = True


    def test_play_playlist_returns_to_completed_page_when_playback_starts(
            self
    ):
        with (
            patch.object(
                app_module.spotify_token_cache,
                "get_cached_token",
                return_value={
                    "access_token": "test-token"
                }
            ),
            patch.object(
                app_module.spotify_service,
                "play_playlist",
                return_value=True
            )
        ):
            response = self.client.post(
                "/play-playlist/playlist123",
                follow_redirects=False
            )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertTrue(
            response.headers["Location"].endswith(
                "/playlist-created/playlist123"
            )
        )


    def test_play_playlist_opens_spotify_when_no_device_available(
            self
    ):
        with (
            patch.object(
                app_module.spotify_token_cache,
                "get_cached_token",
                return_value={
                    "access_token": "test-token"
                }
            ),
            patch.object(
                app_module.spotify_service,
                "play_playlist",
                return_value=False
            )
        ):
            response = self.client.post(
                "/play-playlist/playlist123",
                follow_redirects=False
            )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertEqual(
            response.headers["Location"],
            (
                "https://open.spotify.com/"
                "playlist/playlist123"
            )
        )


    def test_play_playlist_opens_spotify_when_api_error_occurs(
            self
    ):
        spotify_error = SpotifyException(
            http_status=404,
            code=-1,
            msg="Test playback error"
        )

        with (
            patch.object(
                app_module.spotify_token_cache,
                "get_cached_token",
                return_value={
                    "access_token": "test-token"
                }
            ),
            patch.object(
                app_module.spotify_service,
                "play_playlist",
                side_effect=spotify_error
            )
        ):
            response = self.client.post(
                "/play-playlist/playlist123",
                follow_redirects=False
            )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertEqual(
            response.headers["Location"],
            (
                "https://open.spotify.com/"
                "playlist/playlist123"
            )
        )


if __name__ == "__main__":
    unittest.main()