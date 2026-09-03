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

    def test_analyze_track_uses_artist_tags_first(self):
        lastfm_service = MagicMock()

        lastfm_service.get_artist_top_tags.return_value = [
            "rock",
            "pop punk",
        ]

        service = MoodService(
            lastfm_service
        )

        track = {
            "name": "Test Song",
            "artists": ["Test Artist"],
        }

        analyzed = service.analyze_track(
            track
        )

        self.assertEqual(
            analyzed["mood_tag_source"],
            "artist"
        )

        self.assertEqual(
            analyzed["mood_score"],
            47.5
        )

        lastfm_service.get_artist_top_tags.assert_called_once_with(
            "Test Artist"
        )

        # artistタグだけで判定できたので、
        # trackタグは問い合わせない
        lastfm_service.get_track_top_tags.assert_not_called()

    def test_analyze_track_uses_track_tag_cache(self):
        lastfm_service = MagicMock()

        lastfm_service.get_track_top_tags.return_value = [
            "rock",
            "pop punk",
        ]

        service = MoodService(
            lastfm_service
        )

        track = {
            "name": "Still Waiting",
            "artists": ["Sum 41"],
        }

        # 同じ曲を2回解析
        first_result = service.analyze_track(
            track
        )

        second_result = service.analyze_track(
            track
        )

        # 結果はどちらも同じ
        self.assertEqual(
            first_result["mood_score"],
            second_result["mood_score"]
        )

        # Last.fmへの問い合わせは1回だけ
        lastfm_service.get_track_top_tags.assert_called_once_with(
            "Sum 41",
            "Still Waiting"
        )

    def test_analyze_track_uses_artist_tag_cache(self):
        lastfm_service = MagicMock()

        # 曲単位ではどちらもタグが取れない
        lastfm_service.get_track_top_tags.return_value = []

        # アーティストタグは取得できる
        lastfm_service.get_artist_top_tags.return_value = [
            "rock",
            "pop punk",
        ]

        service = MoodService(
            lastfm_service
        )

        first_track = {
            "name": "Song A",
            "artists": ["Sum 41"],
        }

        second_track = {
            "name": "Song B",
            "artists": ["Sum 41"],
        }

        # 同じアーティストの別々の曲を解析
        first_result = service.analyze_track(
            first_track
        )

        second_result = service.analyze_track(
            second_track
        )

        # どちらもartistタグを使っている
        self.assertEqual(
            first_result["mood_tag_source"],
            "artist"
        )

        self.assertEqual(
            second_result["mood_tag_source"],
            "artist"
        )

        # 曲タグ取得は各曲ごとに1回ずつ
        lastfm_service.get_track_top_tags.assert_not_called()

        # アーティストタグ取得は同じSum 41なので1回だけ
        lastfm_service.get_artist_top_tags.assert_called_once_with(
            "Sum 41"
        )

    def test_analyze_track_falls_back_to_track_when_artist_tags_have_no_mood_score(self):
        lastfm_service = MagicMock()

        # artistタグ自体はあるがmood判定できない
        lastfm_service.get_artist_top_tags.return_value = [
            "anime",
            "japanese",
            "soundtrack",
        ]

        # trackタグなら判定できる
        lastfm_service.get_track_top_tags.return_value = [
            "J-rock",
            "alternative",
            "rock",
        ]

        service = MoodService(
            lastfm_service
        )

        track = {
            "name": "Test Song",
            "artists": ["Test Artist"],
        }

        analyzed = service.analyze_track(
            track
        )

        self.assertEqual(
            analyzed["mood_tag_source"],
            "track"
        )

        # alternative=40
        # rock=45
        # J-rockは現在対象外
        self.assertEqual(
            analyzed["mood_score"],
            42.5
        )

        self.assertEqual(
            analyzed["mood_tags"],
            [
                "J-rock",
                "alternative",
                "rock",
            ]
        )

        lastfm_service.get_artist_top_tags.assert_called_once_with(
            "Test Artist"
        )

        lastfm_service.get_track_top_tags.assert_called_once_with(
            "Test Artist",
            "Test Song"
        )

    def test_analyze_artist(self):
        lastfm_service = MagicMock()

        lastfm_service.get_artist_top_tags.return_value = [
            "rock",
            "pop punk",
        ]

        service = MoodService(
            lastfm_service
        )

        analyzed = service.analyze_artist(
            "Sum 41"
        )

        self.assertEqual(
            analyzed["mood_tag_source"],
            "artist"
        )

        self.assertEqual(
            analyzed["mood_score"],
            47.5
        )

        self.assertEqual(
            analyzed["mood_tags"],
            [
                "rock",
                "pop punk",
            ]
        )

        lastfm_service.get_artist_top_tags.assert_called_once_with(
            "Sum 41"
        )

        # analyze_artist() は
        # 曲単位のAPIを使わない
        lastfm_service.get_track_top_tags.assert_not_called()

    def test_analyze_discovered_tracks_reuses_artist_result(self):
        lastfm_service = MagicMock()

        lastfm_service.get_artist_top_tags.return_value = [
            "rock",
            "pop punk",
        ]

        service = MoodService(
            lastfm_service
        )

        tracks = [
            {
                "id": "track1",
                "name": "Song A",
                "artists": ["Sum 41"],
                "discovery_artist": "Sum 41",
            },
            {
                "id": "track2",
                "name": "Song B",
                "artists": ["Sum 41"],
                "discovery_artist": "Sum 41",
            },
            {
                "id": "track3",
                "name": "Song C",
                "artists": ["Sum 41"],
                "discovery_artist": "Sum 41",
            },
        ]

        analyzed_tracks = (
            service.analyze_discovered_tracks(
                tracks
            )
        )

        self.assertEqual(
            len(analyzed_tracks),
            3
        )

        for track in analyzed_tracks:
            self.assertEqual(
                track["mood_score"],
                47.5
            )

            self.assertEqual(
                track["mood_tag_source"],
                "artist"
            )

        # 同じアーティストなので、
        # artistタグ取得は1回だけ
        lastfm_service.get_artist_top_tags.assert_called_once_with(
            "Sum 41"
        )

        # DISCOVEREDではtrackタグを使わない
        lastfm_service.get_track_top_tags.assert_not_called()


if __name__ == "__main__":
    unittest.main()