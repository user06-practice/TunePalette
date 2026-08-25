import unittest
from unittest.mock import MagicMock, patch

from spotify_service import SpotifyService, SpotifyApiSchemaError


class SpotifyServiceTest(unittest.TestCase):

    @patch("spotify_service.spotipy.Spotify")
    def test_get_playlist_tracks(self, mock_spotify_class):
        mock_spotify = MagicMock()
        mock_spotify_class.return_value = mock_spotify

        mock_spotify.playlist_items.return_value = {
            "items": [
                {
                    "item": {
                        "id": "track123",
                        "name": "Test Song",
                        "artists": [
                            {
                                "name": "Test Artist"
                            }
                        ],
                        "uri": "spotify:track:track123"
                    }
                }
            ]
        }

        service = SpotifyService(auth_manager=None)

        tracks = service.get_playlist_tracks("playlist123")

        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0]["name"], "Test Song")
        self.assertEqual(tracks[0]["artists"], ["Test Artist"])
        self.assertEqual(tracks[0]["id"], "track123")

    @patch("spotify_service.spotipy.Spotify")
    def test_get_playlist_tracks_old_track_format(self, mock_spotify_class):
        mock_spotify = MagicMock()
        mock_spotify_class.return_value = mock_spotify

        mock_spotify.playlist_items.return_value = {
            "items": [
                {
                    "track": {
                        "id": "oldtrack123",
                        "name": "Old Test Song",
                        "artists": [
                            {
                                "name": "Old Test Artist"
                            }
                        ],
                        "uri": "spotify:track:oldtrack123"
                    }
                }
            ]
        }

        service = SpotifyService(auth_manager=None)

        tracks = service.get_playlist_tracks("playlist123")

        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0]["name"], "Old Test Song")
        self.assertEqual(tracks[0]["artists"], ["Old Test Artist"])
        self.assertEqual(tracks[0]["id"], "oldtrack123")

    @patch("spotify_service.spotipy.Spotify")
    def test_get_playlist_tracks_unknown_format(self, mock_spotify_class):
        mock_spotify = MagicMock()
        mock_spotify_class.return_value = mock_spotify

        mock_spotify.playlist_items.return_value = {
            "items": [
                {
                    "content": {
                        "name": "Unknown Format"
                    }
                }
            ]
        }

        service = SpotifyService(auth_manager=None)

        with self.assertRaises(SpotifyApiSchemaError):
            service.get_playlist_tracks("playlist123")


if __name__ == "__main__":
    unittest.main()