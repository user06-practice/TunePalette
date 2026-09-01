import unittest
from unittest.mock import MagicMock

from mood_service import MoodService


class MoodServiceTest(unittest.TestCase):

    def test_analyze_track(self):
        lastfm_service = MagicMock()

        lastfm_service.get_track_top_tags.return_value = [
            "punk rock",
            "punk",
            "pop punk",
            "rock",
            "alternative",
            "Energetic",
            "alternative rock",
        ]

        service = MoodService(
            lastfm_service
        )

        track = {
            "id": "track123",
            "name": "Still Waiting",
            "artists": ["Sum 41"],
            "duration_ms": 158000,
            "release_year": 2002,
        }

        analyzed = service.analyze_track(
            track
        )

        self.assertEqual(
            analyzed["name"],
            "Still Waiting"
        )

        self.assertAlmostEqual(
            analyzed["mood_score"],
            52.1
        )

        self.assertIn(
            "pop punk",
            analyzed["mood_tags"]
        )

        lastfm_service.get_track_top_tags.assert_called_once_with(
            "Sum 41",
            "Still Waiting"
        )


    def test_analyze_track_without_known_mood_tags(self):
        lastfm_service = MagicMock()

        lastfm_service.get_track_top_tags.return_value = [
            "Sum 41",
            "Canadian",
            "2002",
        ]

        service = MoodService(
            lastfm_service
        )

        track = {
            "name": "Test Song",
            "artists": ["Sum 41"],
        }

        analyzed = service.analyze_track(
            track
        )

        self.assertIsNone(
            analyzed["mood_score"]
        )


    def test_analyze_track_without_artist(self):
        lastfm_service = MagicMock()

        service = MoodService(
            lastfm_service
        )

        track = {
            "name": "Test Song",
            "artists": [],
        }

        analyzed = service.analyze_track(
            track
        )

        self.assertIsNone(
            analyzed["mood_score"]
        )

        self.assertEqual(
            analyzed["mood_tags"],
            []
        )

        lastfm_service.get_track_top_tags.assert_not_called()


if __name__ == "__main__":
    unittest.main()