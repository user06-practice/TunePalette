import unittest
from unittest.mock import MagicMock

from music_library import MusicLibrary


class MusicLibraryTest(unittest.TestCase):

    def test_get_favorite_tracks(self):
        spotify_service = MagicMock()

        spotify_service.get_playlist_tracks.return_value = [
            {
                "id": "track1",
                "name": "Favorite Song",
                "artists": ["Favorite Artist"],
                "uri": "spotify:track:track1"
            }
        ]

        music_library = MusicLibrary(
            spotify_service,
            "favorite_playlist_123"
        )

        tracks = music_library.get_favorite_tracks()

        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0]["name"], "Favorite Song")

        spotify_service.get_playlist_tracks.assert_called_once_with(
            "favorite_playlist_123",
            limit=50
        )

    def test_favorite_playlist_id_is_required(self):
        spotify_service = MagicMock()

        music_library = MusicLibrary(
            spotify_service,
            None
        )

        with self.assertRaises(ValueError):
            music_library.get_favorite_tracks()

    def test_get_favorite_artists(self):
        spotify_service = MagicMock()

        spotify_service.get_playlist_tracks.return_value = [
            {
                "artists": ["Sum 41"]
            },
            {
                "artists": ["blink-182"]
            },
            {
                "artists": ["Sum 41"]
            },
            {
                "artists": ["Simple Plan", "Mark Hoppus"]
            },
        ]

        music_library = MusicLibrary(
            spotify_service,
            "favorite_playlist_123"
        )

        artists = music_library.get_favorite_artists()

        self.assertEqual(
            artists,
            [
                "Sum 41",
                "blink-182",
                "Simple Plan",
                "Mark Hoppus",
            ]
        )

    def test_get_favorite_artists_ignores_case_duplicates(self):
        spotify_service = MagicMock()

        spotify_service.get_playlist_tracks.return_value = [
            {
                "artists": ["Sum 41"]
            },
            {
                "artists": ["SUM 41"]
            },
        ]

        music_library = MusicLibrary(
            spotify_service,
            "favorite_playlist_123"
        )

        artists = music_library.get_favorite_artists()

        self.assertEqual(
            artists,
            ["Sum 41"]
        )


if __name__ == "__main__":
    unittest.main()