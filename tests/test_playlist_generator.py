import unittest

from playlist_generator import PlaylistGenerator


class PlaylistGeneratorTest(unittest.TestCase):

    def test_decade_weights_at_0(self):
        weights = PlaylistGenerator.get_decade_weights(0)

        self.assertAlmostEqual(weights[1990], 0.20)
        self.assertAlmostEqual(weights[2000], 0.30)
        self.assertAlmostEqual(weights[2010], 0.30)
        self.assertAlmostEqual(weights[2020], 0.20)

    def test_decade_weights_at_50(self):
        weights = PlaylistGenerator.get_decade_weights(50)

        self.assertAlmostEqual(weights[1990], 0.10)
        self.assertAlmostEqual(weights[2000], 0.35)
        self.assertAlmostEqual(weights[2010], 0.35)
        self.assertAlmostEqual(weights[2020], 0.20)

    def test_decade_weights_at_100(self):
        weights = PlaylistGenerator.get_decade_weights(100)

        self.assertAlmostEqual(weights[1990], 0.05)
        self.assertAlmostEqual(weights[2000], 0.10)
        self.assertAlmostEqual(weights[2010], 0.25)
        self.assertAlmostEqual(weights[2020], 0.60)

    def test_decade_weights_at_75(self):
        weights = PlaylistGenerator.get_decade_weights(75)

        self.assertAlmostEqual(weights[1990], 0.075)
        self.assertAlmostEqual(weights[2000], 0.225)
        self.assertAlmostEqual(weights[2010], 0.30)
        self.assertAlmostEqual(weights[2020], 0.40)

    def test_recency_out_of_range(self):
        with self.assertRaises(ValueError):
            PlaylistGenerator.get_decade_weights(101)

    def test_source_time_targets_60_minutes_40_percent(self):
        targets = PlaylistGenerator.get_source_time_targets(
            total_minutes=60,
            discovery_ratio=40
        )

        self.assertEqual(
            targets["favorite_ms"],
            36 * 60 * 1000
        )

        self.assertEqual(
            targets["discovered_ms"],
            24 * 60 * 1000
        )

        self.assertEqual(
            targets["total_ms"],
            60 * 60 * 1000
        )

    def test_source_time_targets_zero_discovery(self):
        targets = PlaylistGenerator.get_source_time_targets(
            total_minutes=60,
            discovery_ratio=0
        )

        self.assertEqual(
            targets["favorite_ms"],
            60 * 60 * 1000
        )

        self.assertEqual(
            targets["discovered_ms"],
            0
        )

    def test_source_time_targets_full_discovery(self):
        targets = PlaylistGenerator.get_source_time_targets(
            total_minutes=60,
            discovery_ratio=100
        )

        self.assertEqual(
            targets["favorite_ms"],
            0
        )

        self.assertEqual(
            targets["discovered_ms"],
            60 * 60 * 1000
        )

    def test_discovery_ratio_out_of_range(self):
        with self.assertRaises(ValueError):
            PlaylistGenerator.get_source_time_targets(
                total_minutes=60,
                discovery_ratio=101
            )

    def test_total_minutes_must_be_positive(self):
        with self.assertRaises(ValueError):
            PlaylistGenerator.get_source_time_targets(
                total_minutes=0,
                discovery_ratio=50
            )

    def test_get_decade(self):
        self.assertEqual(
            PlaylistGenerator.get_decade(1994),
            1990
        )
        self.assertEqual(
            PlaylistGenerator.get_decade(2007),
            2000
        )
        self.assertEqual(
            PlaylistGenerator.get_decade(2018),
            2010
        )
        self.assertEqual(
            PlaylistGenerator.get_decade(2024),
            2020
        )

    def test_get_decade_before_1990(self):
        self.assertIsNone(
            PlaylistGenerator.get_decade(1989)
        )

    def test_select_favorite_tracks(self):
        tracks = [
            {
                "id": "track1",
                "name": "Song 1",
                "artists": ["Artist"],
                "duration_ms": 180000,
                "release_year": 1998,
            },
            {
                "id": "track2",
                "name": "Song 2",
                "artists": ["Artist"],
                "duration_ms": 180000,
                "release_year": 2005,
            },
            {
                "id": "track3",
                "name": "Song 3",
                "artists": ["Artist"],
                "duration_ms": 180000,
                "release_year": 2015,
            },
            {
                "id": "track4",
                "name": "Song 4",
                "artists": ["Artist"],
                "duration_ms": 180000,
                "release_year": 2024,
            },
        ]

        import random

        selected = PlaylistGenerator.select_favorite_tracks(
            tracks=tracks,
            target_ms=9 * 60 * 1000,
            recency=50,
            rng=random.Random(1)
        )

        total_ms = sum(
            track["duration_ms"]
            for track in selected
        )

        self.assertEqual(total_ms, 9 * 60 * 1000)

        # 同じ曲が重複していない
        selected_ids = [
            track["id"]
            for track in selected
        ]

        self.assertEqual(
            len(selected_ids),
            len(set(selected_ids))
        )

    def test_select_favorite_tracks_zero_target(self):
        selected = PlaylistGenerator.select_favorite_tracks(
            tracks=[],
            target_ms=0,
            recency=50
        )

        self.assertEqual(selected, [])

    def test_select_discovered_tracks(self):
        tracks = [
            {
                "id": "track1",
                "duration_ms": 180000,
                "release_year": 2005,
            },
            {
                "id": "track2",
                "duration_ms": 180000,
                "release_year": 2015,
            },
        ]

        selected = (
            PlaylistGenerator.select_discovered_tracks(
                tracks=tracks,
                target_ms=6 * 60 * 1000,
                recency=50
            )
        )

        total_ms = sum(
            track["duration_ms"]
            for track in selected
        )

        self.assertEqual(
            total_ms,
            6 * 60 * 1000
        )

    def test_mix_tracks(self):
        import random

        favorite_tracks = [
            {
                "id": "favorite1",
                "name": "Favorite 1",
            },
            {
                "id": "favorite2",
                "name": "Favorite 2",
            },
        ]

        discovered_tracks = [
            {
                "id": "discovered1",
                "name": "Discovered 1",
            }
        ]

        mixed = PlaylistGenerator.mix_tracks(
            favorite_tracks,
            discovered_tracks,
            rng=random.Random(1)
        )

        self.assertEqual(
            len(mixed),
            3
        )

        ids = {
            track["id"]
            for track in mixed
        }

        self.assertEqual(
            ids,
            {
                "favorite1",
                "favorite2",
                "discovered1"
            }
        )

        favorite_count = sum(
            1
            for track in mixed
            if track["source"] == "FAVORITE"
        )

        discovered_count = sum(
            1
            for track in mixed
            if track["source"] == "DISCOVERED"
        )

        self.assertEqual(
            favorite_count,
            2
        )

        self.assertEqual(
            discovered_count,
            1
        )


if __name__ == "__main__":
    unittest.main()