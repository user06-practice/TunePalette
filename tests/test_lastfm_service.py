import unittest
from unittest.mock import MagicMock, patch

from lastfm_service import (
    LastfmService,
    LastfmApiSchemaError,
)


class LastfmServiceTest(unittest.TestCase):

    @patch("lastfm_service.requests.get")
    def test_get_similar_artists(self, mock_get):
        mock_response = MagicMock()

        mock_response.json.return_value = {
            "similarartists": {
                "artist": [
                    {
                        "name": "blink-182",
                        "match": "0.85"
                    },
                    {
                        "name": "Simple Plan",
                        "match": "0.72"
                    }
                ]
            }
        }

        mock_get.return_value = mock_response

        service = LastfmService("test_api_key")

        artists = service.get_similar_artists(
            "Sum 41",
            limit=10
        )

        self.assertEqual(len(artists), 2)

        self.assertEqual(
            artists[0]["name"],
            "blink-182"
        )

        self.assertAlmostEqual(
            artists[0]["similarity"],
            0.85
        )

        mock_response.raise_for_status.assert_called_once()

    @patch("lastfm_service.requests.get")
    def test_missing_similarartists(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {}

        mock_get.return_value = mock_response

        service = LastfmService("test_api_key")

        with self.assertRaises(LastfmApiSchemaError):
            service.get_similar_artists("Sum 41")

    @patch("lastfm_service.requests.get")
    def test_missing_artist(self, mock_get):
        mock_response = MagicMock()

        mock_response.json.return_value = {
            "similarartists": {}
        }

        mock_get.return_value = mock_response

        service = LastfmService("test_api_key")

        with self.assertRaises(LastfmApiSchemaError):
            service.get_similar_artists("Sum 41")

    @patch("lastfm_service.requests.get")
    def test_artist_missing_required_fields(self, mock_get):
        mock_response = MagicMock()

        mock_response.json.return_value = {
            "similarartists": {
                "artist": [
                    {
                        "name": "blink-182"
                    }
                ]
            }
        }

        mock_get.return_value = mock_response

        service = LastfmService("test_api_key")

        with self.assertRaises(LastfmApiSchemaError):
            service.get_similar_artists("Sum 41")

    @patch("lastfm_service.requests.get")
    def test_get_track_top_tags(self, mock_get):
        mock_response = MagicMock()

        mock_response.json.return_value = {
            "toptags": {
                "tag": [
                    {
                        "name": "pop punk"
                    },
                    {
                        "name": "punk rock"
                    },
                    {
                        "name": "rock"
                    }
                ]
            }
        }

        mock_get.return_value = mock_response

        service = LastfmService("test_api_key")

        tags = service.get_track_top_tags(
            "Sum 41",
            "Still Waiting"
        )

        self.assertEqual(
            tags,
            [
                "pop punk",
                "punk rock",
                "rock",
            ]
        )

        mock_response.raise_for_status.assert_called_once()

    @patch("lastfm_service.requests.get")
    def test_get_track_top_tags_missing_toptags(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {}

        mock_get.return_value = mock_response

        service = LastfmService("test_api_key")

        with self.assertRaises(
                LastfmApiSchemaError
        ):
            service.get_track_top_tags(
                "Sum 41",
                "Still Waiting"
            )

    @patch("lastfm_service.requests.get")
    def test_get_track_top_tags_missing_tag_name(self, mock_get):
        mock_response = MagicMock()

        mock_response.json.return_value = {
            "toptags": {
                "tag": [
                    {}
                ]
            }
        }

        mock_get.return_value = mock_response

        service = LastfmService("test_api_key")

        with self.assertRaises(
                LastfmApiSchemaError
        ):
            service.get_track_top_tags(
                "Sum 41",
                "Still Waiting"
            )

    @patch("lastfm_service.requests.get")
    def test_get_artist_top_tags(self, mock_get):
        mock_response = MagicMock()

        mock_response.json.return_value = {
            "toptags": {
                "tag": [
                    {"name": "j-rock"},
                    {"name": "alternative rock"},
                    {"name": "japanese"},
                ]
            }
        }

        mock_get.return_value = mock_response

        service = LastfmService("test_api_key")

        tags = service.get_artist_top_tags(
            "TK from Ling tosite sigure"
        )

        self.assertEqual(
            tags,
            [
                "j-rock",
                "alternative rock",
                "japanese",
            ]
        )

        mock_response.raise_for_status.assert_called_once()

    @patch("lastfm_service.requests.get")
    def test_get_artist_top_tags_missing_toptags(
            self,
            mock_get
    ):
        mock_response = MagicMock()
        mock_response.json.return_value = {}

        mock_get.return_value = mock_response

        service = LastfmService("test_api_key")

        with self.assertRaises(
                LastfmApiSchemaError
        ):
            service.get_artist_top_tags(
                "TK from Ling tosite sigure"
            )

    @patch("lastfm_service.requests.get")
    def test_get_artist_top_tags_returns_empty_on_rate_limit(
            self,
            mock_get
    ):
        mock_response = MagicMock()

        mock_response.json.return_value = {
            "error": 29,
            "message": "Rate limit exceeded"
        }

        mock_get.return_value = mock_response

        service = LastfmService(
            "test_api_key"
        )

        tags = service.get_artist_top_tags(
            "Sum 41"
        )

        self.assertEqual(
            tags,
            []
        )

        mock_response.raise_for_status.assert_called_once()

    @patch("lastfm_service.requests.get")
    def test_get_track_top_tags_returns_empty_on_rate_limit(
            self,
            mock_get
    ):
        mock_response = MagicMock()

        mock_response.json.return_value = {
            "error": 29,
            "message": "Rate limit exceeded"
        }

        mock_get.return_value = mock_response

        service = LastfmService(
            "test_api_key"
        )

        tags = service.get_track_top_tags(
            "Sum 41",
            "Still Waiting"
        )

        self.assertEqual(
            tags,
            []
        )

        mock_response.raise_for_status.assert_called_once()


if __name__ == "__main__":
    unittest.main()