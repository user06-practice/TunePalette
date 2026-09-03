import random


class PlaylistGenerator:

    @staticmethod
    def get_decade(release_year):
        if release_year is None or release_year < 1990:
            return None

        if release_year >= 2020:
            return 2020

        return (release_year // 10) * 10

    @staticmethod
    def get_mood_weight(track_mood_score, mood):
        if not 0 <= mood <= 100:
            raise ValueError(
                "moodは0～100で指定してください。"
            )

        # mood_scoreを判定できなかった曲も
        # 完全には候補から除外しない
        if track_mood_score is None:
            return 0.25

        difference = abs(
            mood - track_mood_score
        )

        weight = 1.0 - (
                difference / 100
        )

        return max(
            weight,
            0.05
        )

    @classmethod
    def select_tracks(
            cls,
            tracks,
            target_ms,
            recency,
            mood=50,
            rng=None,
            max_tracks_per_artist=None
    ):
        if target_ms < 0:
            raise ValueError("target_msは0以上で指定してください。")

        if target_ms == 0:
            return []

        if rng is None:
            rng = random.Random()

        decade_weights = cls.get_decade_weights(recency)

        # 再生時間・年代が選曲に使える曲だけ候補にする
        available_tracks = [
            track
            for track in tracks
            if track.get("duration_ms")
               and cls.get_decade(
                track.get("release_year")
            ) in decade_weights
        ]

        selected_tracks = []
        total_ms = 0

        selected_artist_counts = {}

        while available_tracks and total_ms < target_ms:
            eligible_tracks = []

            for track in available_tracks:

                if max_tracks_per_artist is not None:
                    artist_name = track.get(
                        "discovery_artist"
                    )

                    # discovery_artistがない場合の保険
                    if not artist_name:
                        artists = track.get(
                            "artists",
                            []
                        )

                        if artists:
                            artist_name = artists[0]

                    if artist_name:
                        artist_key = artist_name.casefold()

                        if (
                                selected_artist_counts.get(
                                    artist_key,
                                    0
                                )
                                >= max_tracks_per_artist
                        ):
                            continue

                eligible_tracks.append(track)

            if not eligible_tracks:
                break

            tracks_by_decade = {}

            for track in eligible_tracks:
                decade = cls.get_decade(
                    track["release_year"]
                )

                tracks_by_decade.setdefault(
                    decade,
                    []
                ).append(track)

            available_decades = list(
                tracks_by_decade.keys()
            )

            selected_decade = rng.choices(
                available_decades,
                weights=[
                    decade_weights[decade]
                    for decade in available_decades
                ],
                k=1
            )[0]

            decade_tracks = tracks_by_decade[
                selected_decade
            ]

            track = rng.choices(
                decade_tracks,
                weights=[
                    cls.get_mood_weight(
                        track.get("mood_score"),
                        mood
                    )
                    for track in decade_tracks
                ],
                k=1
            )[0]

            available_tracks.remove(track)

            duration_ms = track["duration_ms"]

            current_difference = abs(
                target_ms - total_ms
            )

            next_difference = abs(
                target_ms - (
                        total_ms + duration_ms
                )
            )

            if next_difference <= current_difference:
                selected_tracks.append(track)
                total_ms += duration_ms

                if max_tracks_per_artist is not None:
                    artist_name = track.get(
                        "discovery_artist"
                    )

                    if not artist_name:
                        artists = track.get(
                            "artists",
                            []
                        )

                        if artists:
                            artist_name = artists[0]

                    if artist_name:
                        artist_key = artist_name.casefold()

                        selected_artist_counts[
                            artist_key
                        ] = (
                                selected_artist_counts.get(
                                    artist_key,
                                    0
                                )
                                + 1
                        )

        return selected_tracks

    @classmethod
    def select_favorite_tracks(
            cls,
            tracks,
            target_ms,
            recency,
            mood=50,
            rng=None
    ):
        return cls.select_tracks(
            tracks=tracks,
            target_ms=target_ms,
            recency=recency,
            mood=mood,
            rng=rng
        )

    @classmethod
    def select_discovered_tracks(
            cls,
            tracks,
            target_ms,
            recency,
            mood=50,
            rng=None
    ):
        return cls.select_tracks(
            tracks=tracks,
            target_ms=target_ms,
            recency=recency,
            mood=mood,
            rng=rng,
            max_tracks_per_artist=2
        )

    @staticmethod
    def get_decade_weights(recency):
        if not 0 <= recency <= 100:
            raise ValueError("recencyは0～100で指定してください。")

        weights_0 = {
            1990: 0.20,
            2000: 0.30,
            2010: 0.30,
            2020: 0.20,
        }

        weights_50 = {
            1990: 0.10,
            2000: 0.35,
            2010: 0.35,
            2020: 0.20,
        }

        weights_100 = {
            1990: 0.05,
            2000: 0.10,
            2010: 0.25,
            2020: 0.60,
        }

        if recency <= 50:
            start = weights_0
            end = weights_50
            ratio = recency / 50
        else:
            start = weights_50
            end = weights_100
            ratio = (recency - 50) / 50

        return {
            decade: start[decade] + (
                end[decade] - start[decade]
            ) * ratio
            for decade in start
        }

    @staticmethod
    def get_source_time_targets(total_minutes, discovery_ratio):
        if total_minutes <= 0:
            raise ValueError("再生時間は1分以上で指定してください。")

        if not 0 <= discovery_ratio <= 100:
            raise ValueError(
                "discovery_ratioは0～100で指定してください。"
            )

        total_ms = total_minutes * 60 * 1000

        discovered_ms = int(
            total_ms * discovery_ratio / 100
        )

        favorite_ms = total_ms - discovered_ms

        return {
            "favorite_ms": favorite_ms,
            "discovered_ms": discovered_ms,
            "total_ms": total_ms,
        }

    @staticmethod
    def mix_tracks(
            favorite_tracks,
            discovered_tracks,
            rng=None
    ):
        if rng is None:
            rng = random.Random()

        mixed_tracks = []

        for track in favorite_tracks:
            mixed_tracks.append({
                **track,
                "source": "FAVORITE"
            })

        for track in discovered_tracks:
            mixed_tracks.append({
                **track,
                "source": "DISCOVERED"
            })

        rng.shuffle(mixed_tracks)

        return mixed_tracks