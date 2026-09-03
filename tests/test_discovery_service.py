import unittest
from unittest.mock import MagicMock

from discovery_service import DiscoveryService


class DiscoveryServiceTest(unittest.TestCase):

    def test_get_candidate_artists(self):
        music_library = MagicMock()
        lastfm_service = MagicMock()
        rng = MagicMock()

        music_library.get_favorite_artists.return_value = [
            "Sum 41",
            "blink-182",
            "Green Day",
        ]

        rng.sample.return_value = [
            "Sum 41",
            "blink-182",
        ]

        lastfm_service.get_similar_artists.side_effect = [
            [
                {
                    "name": "Simple Plan",
                    "similarity": 0.80,
                },
                {
                    "name": "Zebrahead",
                    "similarity": 0.70,
                },
            ],
            [
                {
                    "name": "Simple Plan",
                    "similarity": 0.90,
                },
                {
                    "name": "Box Car Racer",
                    "similarity": 0.75,
                },
            ],
        ]

        spotify_service = MagicMock()
        service = DiscoveryService(
            music_library,
            lastfm_service,
            spotify_service
        )

        candidates = service.get_candidate_artists(
            seed_limit=2,
            similar_limit=10,
            rng=rng
        )

        # Simple Planは重複するので全部で3組
        self.assertEqual(
            len(candidates),
            3
        )

        simple_plan = next(
            artist
            for artist in candidates
            if artist["name"] == "Simple Plan"
        )

        # 高い方の類似度が残る
        self.assertAlmostEqual(
            simple_plan["similarity"],
            0.90
        )

        # 2つのFAVORITEを起点に見つかった
        self.assertEqual(
            simple_plan["source_artists"],
            [
                "Sum 41",
                "blink-182",
            ]
        )


    def test_seed_limit_reduces_api_calls(self):
        music_library = MagicMock()
        lastfm_service = MagicMock()
        rng = MagicMock()

        music_library.get_favorite_artists.return_value = [
            "Artist A",
            "Artist B",
            "Artist C",
            "Artist D",
        ]

        rng.sample.return_value = [
            "Artist A",
            "Artist B",
        ]

        lastfm_service.get_similar_artists.return_value = []

        spotify_service = MagicMock()
        service = DiscoveryService(
            music_library,
            lastfm_service,
            spotify_service
        )

        service.get_candidate_artists(
            seed_limit=2,
            similar_limit=10,
            rng=rng
        )

        self.assertEqual(
            lastfm_service.get_similar_artists.call_count,
            2
        )


    def test_no_favorite_artists(self):
        music_library = MagicMock()
        lastfm_service = MagicMock()

        music_library.get_favorite_artists.return_value = []

        spotify_service = MagicMock()
        service = DiscoveryService(
            music_library,
            lastfm_service,
            spotify_service
        )

        candidates = service.get_candidate_artists()

        self.assertEqual(candidates, [])

        lastfm_service.get_similar_artists.assert_not_called()

    def test_get_candidate_tracks_excludes_favorites_and_duplicates(self):
        music_library = MagicMock()
        lastfm_service = MagicMock()
        spotify_service = MagicMock()

        music_library.get_favorite_tracks.return_value = [
            {
                "id": "favorite1",
                "name": "Favorite Song",
                "artists": ["Simple Plan"],
            }
        ]

        candidate_artists = [
            {
                "name": "Simple Plan",
                "similarity": 0.90,
                "source_artists": ["Sum 41"],
            },
            {
                "name": "Zebrahead",
                "similarity": 0.80,
                "source_artists": ["Sum 41"],
            },
        ]

        spotify_service.search_tracks_by_artist.side_effect = [
            [
                {
                    "id": "favorite1",
                    "name": "Favorite Song",
                    "artists": ["Simple Plan"],
                },
                {
                    "id": "new1",
                    "name": "New Song 1",
                    "artists": ["Simple Plan"],
                },
                {
                    "id": "shared1",
                    "name": "Shared Song",
                    "artists": ["Simple Plan", "Zebrahead"],
                },
            ],
            [
                {
                    "id": "shared1",
                    "name": "Shared Song",
                    "artists": ["Simple Plan", "Zebrahead"],
                },
                {
                    "id": "new2",
                    "name": "New Song 2",
                    "artists": ["Zebrahead"],
                },
            ],
        ]

        service = DiscoveryService(
            music_library,
            lastfm_service,
            spotify_service
        )

        tracks = service.get_candidate_tracks(
            candidate_artists,
            artist_limit=10,
            tracks_per_artist=10
        )

        track_ids = [
            track["id"]
            for track in tracks
        ]

        # FAVORITE曲は除外
        self.assertNotIn(
            "favorite1",
            track_ids
        )

        # 新しい曲は残る
        self.assertIn(
            "new1",
            track_ids
        )

        self.assertIn(
            "new2",
            track_ids
        )

        # shared1は2回出てきても1曲だけ
        self.assertEqual(
            track_ids.count("shared1"),
            1
        )

    def test_get_candidate_tracks_ignores_wrong_artist(self):
        music_library = MagicMock()
        lastfm_service = MagicMock()
        spotify_service = MagicMock()

        music_library.get_favorite_tracks.return_value = []

        candidate_artists = [
            {
                "name": "Simple Plan",
                "similarity": 0.90,
                "source_artists": ["Sum 41"],
            }
        ]

        # Spotify検索に別アーティストの曲が混ざった想定
        spotify_service.search_tracks_by_artist.return_value = [
            {
                "id": "wrong1",
                "name": "Wrong Song",
                "artists": ["Other Artist"],
            }
        ]

        service = DiscoveryService(
            music_library,
            lastfm_service,
            spotify_service
        )

        tracks = service.get_candidate_tracks(
            candidate_artists
        )

        self.assertEqual(
            tracks,
            []
        )

    def test_get_candidate_tracks_limits_artist_searches(self):
        music_library = MagicMock()
        lastfm_service = MagicMock()
        spotify_service = MagicMock()

        music_library.get_favorite_tracks.return_value = []

        candidate_artists = [
            {
                "name": "Artist A",
                "similarity": 0.90,
                "source_artists": ["Seed"],
            },
            {
                "name": "Artist B",
                "similarity": 0.80,
                "source_artists": ["Seed"],
            },
            {
                "name": "Artist C",
                "similarity": 0.70,
                "source_artists": ["Seed"],
            },
        ]

        spotify_service.search_tracks_by_artist.return_value = []

        service = DiscoveryService(
            music_library,
            lastfm_service,
            spotify_service
        )

        service.get_candidate_tracks(
            candidate_artists,
            artist_limit=2,
            tracks_per_artist=10
        )

        # 3組候補がいても上位2組までしかSpotify検索しない
        self.assertEqual(
            spotify_service.search_tracks_by_artist.call_count,
            2
        )

    def test_get_candidate_tracks_tracks_per_artist_out_of_range(self):
        music_library = MagicMock()
        lastfm_service = MagicMock()
        spotify_service = MagicMock()

        service = DiscoveryService(
            music_library,
            lastfm_service,
            spotify_service
        )

        with self.assertRaises(ValueError):
            service.get_candidate_tracks(
                candidate_artists=[],
                tracks_per_artist=11
            )

    def test_get_candidate_tracks_excludes_same_title_and_artist_with_different_ids(self):
        music_library = MagicMock()
        lastfm_service = MagicMock()
        spotify_service = MagicMock()

        music_library.get_favorite_tracks.return_value = []

        candidate_artists = [
            {
                "name": "Linked Horizon",
                "similarity": 0.90,
                "source_artists": ["Seed Artist"],
            }
        ]

        spotify_service.search_tracks_by_artist.return_value = [
            {
                "id": "track2013",
                "name": "紅蓮の弓矢",
                "artists": ["Linked Horizon"],
            },
            {
                "id": "track2017",
                "name": "紅蓮の弓矢",
                "artists": ["Linked Horizon"],
            },
        ]

        service = DiscoveryService(
            music_library,
            lastfm_service,
            spotify_service
        )

        tracks = service.get_candidate_tracks(
            candidate_artists
        )

        self.assertEqual(
            len(tracks),
            1
        )

        self.assertEqual(
            tracks[0]["name"],
            "紅蓮の弓矢"
        )


if __name__ == "__main__":
    unittest.main()