class MoodScorer:

    TAG_SCORES = {
        # 落ち着く側
        "ambient": 5,
        "chill": 10,
        "mellow": 15,
        "acoustic": 20,
        "ballad": 25,
        "soft rock": 30,

        # 中間
        "pop": 35,
        "indie": 35,
        "pop rock": 40,
        "indie rock": 40,
        "alternative": 40,
        "rock": 45,
        "alternative rock": 45,

        # TunePaletteの基準点
        "pop punk": 50,

        # 激しめ側
        "punk": 60,
        "punk rock": 60,
        "energetic": 65,
        "hard rock": 65,
        "hardcore": 70,
        "post-hardcore": 70,
        "metalcore": 75,
        "heavy metal": 80,
        "metal": 80,
        "death metal": 100,
    }

    @classmethod
    def score_tags(cls, tags):
        scores = []

        for tag in tags:
            normalized_tag = tag.strip().casefold()

            if normalized_tag in cls.TAG_SCORES:
                scores.append(
                    cls.TAG_SCORES[normalized_tag]
                )

        if not scores:
            return None

        return round(
            sum(scores) / len(scores),
            1
        )