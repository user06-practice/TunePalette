import unittest

from mood_scorer import MoodScorer


class MoodScorerTest(unittest.TestCase):

    def test_score_still_waiting_tags(self):
        tags = [
            "punk rock",
            "punk",
            "pop punk",
            "rock",
            "sum 41",
            "alternative",
            "Canadian",
            "Energetic",
            "alternative rock",
            "2002",
        ]

        score = MoodScorer.score_tags(tags)

        self.assertAlmostEqual(
            score,
            52.1
        )

    def test_unknown_tags_are_ignored(self):
        tags = [
            "pop punk",
            "Sum 41",
            "Canadian",
            "2002",
        ]

        score = MoodScorer.score_tags(tags)

        self.assertEqual(
            score,
            50.0
        )

    def test_no_known_tags_returns_none(self):
        tags = [
            "Sum 41",
            "Canadian",
            "2002",
        ]

        score = MoodScorer.score_tags(tags)

        self.assertIsNone(score)

    def test_death_metal_is_maximum(self):
        score = MoodScorer.score_tags(
            ["death metal"]
        )

        self.assertEqual(
            score,
            100.0
        )


if __name__ == "__main__":
    unittest.main()