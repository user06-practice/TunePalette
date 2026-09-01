import os
import unittest

from dotenv import load_dotenv

from lastfm_service import LastfmService


load_dotenv()


@unittest.skipUnless(
    os.getenv("RUN_LASTFM_INTEGRATION_TESTS") == "1",
    "Last.fm統合テストは通常は実行しません。"
)
class LastfmIntegrationTest(unittest.TestCase):

    def test_get_real_similar_artists(self):
        api_key = os.getenv("LASTFM_API_KEY")

        self.assertTrue(
            api_key,
            "LASTFM_API_KEYが設定されていません。"
        )

        service = LastfmService(api_key)

        artists = service.get_similar_artists(
            "Sum 41",
            limit=5
        )

        self.assertGreater(len(artists), 0)

        for artist in artists:
            self.assertTrue(artist["name"])

            self.assertGreaterEqual(
                artist["similarity"],
                0.0
            )

            self.assertLessEqual(
                artist["similarity"],
                1.0
            )

    def test_get_real_track_top_tags(self):
        api_key = os.getenv("LASTFM_API_KEY")

        self.assertTrue(
            api_key,
            "LASTFM_API_KEYが設定されていません。"
        )

        service = LastfmService(api_key)

        tags = service.get_track_top_tags(
            "Sum 41",
            "Still Waiting"
        )

        self.assertIsInstance(
            tags,
            list
        )

        self.assertGreater(
            len(tags),
            0
        )

        for tag in tags:
            self.assertIsInstance(
                tag,
                str
            )

            self.assertTrue(tag)

        print("取得したタグ:", tags)

    def test_get_real_artist_top_tags(self):
        api_key = os.getenv("LASTFM_API_KEY")

        self.assertTrue(
            api_key,
            "LASTFM_API_KEYが設定されていません。"
        )

        service = LastfmService(api_key)

        artist_names = [
            "LiSA",
            "TK from Ling tosite sigure",
            "μ's",
        ]

        found_any_tags = False

        for artist_name in artist_names:
            tags = service.get_artist_top_tags(
                artist_name
            )

            self.assertIsInstance(
                tags,
                list
            )

            if tags:
                found_any_tags = True

            print(
                f"{artist_name} のタグ:",
                tags
            )

        self.assertTrue(
            found_any_tags,
            "3組すべてでアーティストタグを取得できませんでした。"
        )


if __name__ == "__main__":
    unittest.main()