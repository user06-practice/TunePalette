import os
import unittest
from unittest.mock import MagicMock, patch


# app.pyをimportする前に、テスト用の環境変数を設定する
os.environ.setdefault("FLASK_SECRET_KEY", "test-secret-key")
os.environ.setdefault("SPOTIFY_CLIENT_ID", "test-client-id")
os.environ.setdefault("SPOTIFY_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault(
    "SPOTIFY_REDIRECT_URI",
    "http://127.0.0.1:5000/callback"
)
os.environ.setdefault(
    "SPOTIFY_ALLOWED_ACCOUNT_ID",
    "allowed-account"
)

import app as app_module


class AuthTest(unittest.TestCase):

    def setUp(self):
        app_module.app.config["TESTING"] = True
        app_module.app.config["SECRET_KEY"] = "test-secret-key"

        self.client = app_module.app.test_client()

    def test_playlists_requires_authorized_session(self):
        response = self.client.get(
            "/playlists",
            follow_redirects=False
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response.headers["Location"].endswith("/login")
        )

    def test_playlists_requires_spotify_token(self):
        # ブラウザ側だけ本人確認済みの状態にする
        with self.client.session_transaction() as session:
            session["authorized"] = True

        # サーバー側のTokenが消えた状態を再現
        with patch.object(
            app_module.spotify_token_cache,
            "get_cached_token",
            return_value=None
        ):
            response = self.client.get(
                "/playlists",
                follow_redirects=False
            )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response.headers["Location"].endswith("/login")
        )

        # Tokenが無い場合は古い認証済みsessionも削除される
        with self.client.session_transaction() as session:
            self.assertNotIn("authorized", session)

    def test_callback_rejects_other_account(self):
        temporary_cache = MagicMock()
        temporary_cache.get_cached_token.return_value = {
            "access_token": "test-token"
        }

        temporary_oauth = MagicMock()

        temporary_service = MagicMock()
        temporary_service.get_current_account.return_value = {
            "account_id": "different-account",
            "display_name": "Other User"
        }

        with (
            patch.object(
                app_module,
                "MemoryCacheHandler",
                return_value=temporary_cache
            ),
            patch.object(
                app_module,
                "SpotifyOAuth",
                return_value=temporary_oauth
            ),
            patch.object(
                app_module,
                "SpotifyService",
                return_value=temporary_service
            ),
            patch.object(
                app_module.spotify_token_cache,
                "save_token_to_cache"
            ) as save_token
        ):
            response = self.client.get(
                "/callback?code=test-code"
            )

        self.assertEqual(response.status_code, 403)

        # 他人のTokenは正式保存されない
        save_token.assert_not_called()

        with self.client.session_transaction() as session:
            self.assertNotIn("authorized", session)

    def test_callback_allows_registered_account(self):
        token_info = {
            "access_token": "test-token"
        }

        temporary_cache = MagicMock()
        temporary_cache.get_cached_token.return_value = token_info

        temporary_oauth = MagicMock()

        temporary_service = MagicMock()
        temporary_service.get_current_account.return_value = {
            "account_id": "allowed-account",
            "display_name": "Test User"
        }

        with (
            patch.object(
                app_module,
                "MemoryCacheHandler",
                return_value=temporary_cache
            ),
            patch.object(
                app_module,
                "SpotifyOAuth",
                return_value=temporary_oauth
            ),
            patch.object(
                app_module,
                "SpotifyService",
                return_value=temporary_service
            ),
            patch.object(
                app_module.spotify_token_cache,
                "save_token_to_cache"
            ) as save_token
        ):
            response = self.client.get(
                "/callback?code=test-code",
                follow_redirects=False
            )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response.headers["Location"].endswith("/settings")
        )

        # 本人のTokenだけ正式なメモリキャッシュへ保存
        save_token.assert_called_once_with(token_info)

        # このブラウザsessionが本人確認済みになる
        with self.client.session_transaction() as session:
            self.assertTrue(session["authorized"])


if __name__ == "__main__":
    unittest.main()