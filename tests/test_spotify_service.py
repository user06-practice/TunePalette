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
                        "uri": "spotify:track:track123",
                        "duration_ms": 215000,
                        "album": {
                            "release_date": "2022-06-15"
                        }
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
        self.assertEqual(tracks[0]["duration_ms"], 215000)
        self.assertEqual(tracks[0]["release_date"], "2022-06-15")
        self.assertEqual(tracks[0]["release_year"], 2022)

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

    @patch("spotify_service.spotipy.Spotify")
    def test_get_playlist_tracks_multiple_pages(self, mock_spotify_class):
        mock_spotify = MagicMock()
        mock_spotify_class.return_value = mock_spotify

        first_page = {
            "items": [
                {
                    "item": {
                        "id": "track1",
                        "name": "Song 1",
                        "artists": [{"name": "Artist 1"}],
                        "uri": "spotify:track:track1"
                    }
                },
                {
                    "item": {
                        "id": "track2",
                        "name": "Song 2",
                        "artists": [{"name": "Artist 2"}],
                        "uri": "spotify:track:track2"
                    }
                }
            ]
        }

        second_page = {
            "items": [
                {
                    "item": {
                        "id": "track3",
                        "name": "Song 3",
                        "artists": [{"name": "Artist 3"}],
                        "uri": "spotify:track:track3"
                    }
                }
            ]
        }

        mock_spotify.playlist_items.side_effect = [
            first_page,
            second_page
        ]

        service = SpotifyService(auth_manager=None)

        tracks = service.get_playlist_tracks(
            "playlist123",
            limit=2
        )

        self.assertEqual(len(tracks), 3)

        self.assertEqual(tracks[0]["name"], "Song 1")
        self.assertEqual(tracks[1]["name"], "Song 2")
        self.assertEqual(tracks[2]["name"], "Song 3")

        self.assertEqual(
            mock_spotify.playlist_items.call_count,
            2
        )

    @patch("spotify_service.spotipy.Spotify")
    def test_search_tracks_by_artist(self, mock_spotify_class):
        mock_spotify = MagicMock()
        mock_spotify_class.return_value = mock_spotify

        mock_spotify.search.return_value = {
            "tracks": {
                "items": [
                    {
                        "id": "track123",
                        "name": "Test Song",
                        "artists": [
                            {
                                "name": "Simple Plan"
                            }
                        ],
                        "uri": "spotify:track:track123",
                        "duration_ms": 180000,
                        "album": {
                            "release_date": "2022-05-01"
                        }
                    }
                ]
            }
        }

        service = SpotifyService(auth_manager=None)

        tracks = service.search_tracks_by_artist(
            "Simple Plan",
            limit=10
        )

        self.assertEqual(len(tracks), 1)
        self.assertEqual(
            tracks[0]["name"],
            "Test Song"
        )
        self.assertEqual(
            tracks[0]["artists"],
            ["Simple Plan"]
        )
        self.assertEqual(
            tracks[0]["release_year"],
            2022
        )

    @patch("spotify_service.spotipy.Spotify")
    def test_search_tracks_missing_tracks(self, mock_spotify_class):
        mock_spotify = MagicMock()
        mock_spotify_class.return_value = mock_spotify

        mock_spotify.search.return_value = {}

        service = SpotifyService(auth_manager=None)

        with self.assertRaises(
                SpotifyApiSchemaError
        ):
            service.search_tracks_by_artist(
                "Simple Plan"
            )

    @patch("spotify_service.spotipy.Spotify")
    def test_search_tracks_limit_out_of_range(self, mock_spotify_class):
        mock_spotify = MagicMock()
        mock_spotify_class.return_value = mock_spotify

        service = SpotifyService(auth_manager=None)

        with self.assertRaises(ValueError):
            service.search_tracks_by_artist(
                "Simple Plan",
                limit=11
            )

    @patch("spotify_service.spotipy.Spotify")
    def test_create_playlist(self, mock_spotify_class):
        mock_spotify = MagicMock()
        mock_spotify_class.return_value = mock_spotify

        mock_spotify.current_user_playlist_create.return_value = {
            "id": "playlist123",
            "name": "TunePalette Test",
            "uri": "spotify:playlist:playlist123",
        }

        service = SpotifyService(auth_manager=None)

        playlist = service.create_playlist(
            name="TunePalette Test",
            public=False,
            description="TunePalette generated playlist"
        )

        self.assertEqual(
            playlist["id"],
            "playlist123"
        )

        self.assertEqual(
            playlist["name"],
            "TunePalette Test"
        )

    @patch("spotify_service.spotipy.Spotify")
    def test_create_playlist_missing_id(self, mock_spotify_class):
        mock_spotify = MagicMock()
        mock_spotify_class.return_value = mock_spotify

        mock_spotify.current_user_playlist_create.return_value = {}

        service = SpotifyService(auth_manager=None)

        with self.assertRaises(
                SpotifyApiSchemaError
        ):
            service.create_playlist(
                "TunePalette Test"
            )

    @patch("spotify_service.spotipy.Spotify")
    def test_add_tracks_to_playlist(self, mock_spotify_class):
        mock_spotify = MagicMock()
        mock_spotify_class.return_value = mock_spotify

        service = SpotifyService(auth_manager=None)

        tracks = [
            {
                "uri": "spotify:track:track1"
            },
            {
                "uri": "spotify:track:track2"
            },
        ]

        service.add_tracks_to_playlist(
            "playlist123",
            tracks
        )

        mock_spotify.playlist_add_items.assert_called_once_with(
            "playlist123",
            [
                "spotify:track:track1",
                "spotify:track:track2",
            ]
        )

    @patch("spotify_service.spotipy.Spotify")
    def test_add_tracks_to_playlist_splits_batches(
            self,
            mock_spotify_class
    ):
        mock_spotify = MagicMock()
        mock_spotify_class.return_value = mock_spotify

        service = SpotifyService(auth_manager=None)

        tracks = [
            {
                "uri": f"spotify:track:track{i}"
            }
            for i in range(101)
        ]

        service.add_tracks_to_playlist(
            "playlist123",
            tracks
        )

        self.assertEqual(
            mock_spotify.playlist_add_items.call_count,
            2
        )


if __name__ == "__main__":
    unittest.main()
