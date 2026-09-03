from mood_scorer import MoodScorer


class MoodService:

    def __init__(self, lastfm_service):
        self.lastfm_service = lastfm_service

        # Last.fmへの同じ問い合わせを繰り返さないための
        # メモリ上のキャッシュ
        self.track_tag_cache = {}
        self.artist_tag_cache = {}

    def get_cached_track_tags(
            self,
            artist_name,
            track_name
    ):
        cache_key = (
            artist_name.casefold(),
            track_name.casefold()
        )

        if cache_key not in self.track_tag_cache:
            self.track_tag_cache[cache_key] = (
                self.lastfm_service.get_track_top_tags(
                    artist_name,
                    track_name
                )
            )

        return self.track_tag_cache[cache_key]

    def get_cached_artist_tags(
            self,
            artist_name
    ):
        cache_key = artist_name.casefold()

        if cache_key not in self.artist_tag_cache:
            self.artist_tag_cache[cache_key] = (
                self.lastfm_service.get_artist_top_tags(
                    artist_name
                )
            )

        return self.artist_tag_cache[cache_key]

    def analyze_artist(self, artist_name):

        if not artist_name:
            return {
                "mood_tags": [],
                "mood_score": None,
                "mood_tag_source": None,
            }

        # キャッシュを利用してアーティストタグを取得
        tags = self.get_cached_artist_tags(
            artist_name
        )

        mood_score = MoodScorer.score_tags(
            tags
        )

        return {
            "mood_tags": tags,
            "mood_score": mood_score,
            "mood_tag_source": "artist",
        }

    def analyze_discovered_tracks(self, tracks):
        analyzed_tracks = []

        # 同じ処理の中でも、
        # 同一アーティストのmood判定を繰り返さない
        artist_results = {}

        for track in tracks:
            # DiscoveryServiceが付けている
            # DISCOVERED候補アーティスト名を使用
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

            # アーティスト名自体が取得できない場合
            if not artist_name:
                analyzed_tracks.append({
                    **track,
                    "mood_tags": [],
                    "mood_score": None,
                    "mood_tag_source": None,
                })

                continue

            cache_key = artist_name.casefold()

            # 同じアーティストは1回だけ解析
            if cache_key not in artist_results:
                artist_results[cache_key] = (
                    self.analyze_artist(
                        artist_name
                    )
                )

            mood_result = artist_results[
                cache_key
            ]

            analyzed_tracks.append({
                **track,
                "mood_tags": mood_result[
                    "mood_tags"
                ],
                "mood_score": mood_result[
                    "mood_score"
                ],
                "mood_tag_source": mood_result[
                    "mood_tag_source"
                ],
            })

        return analyzed_tracks

    def analyze_track(self, track):

        track_name = track.get("name")
        artists = track.get("artists", [])

        # 曲名やアーティスト名がない場合
        if not track_name or not artists:
            return {
                **track,
                "mood_tags": [],
                "mood_score": None,
                "mood_tag_source": None,
            }

        # Spotifyでは複数アーティストの場合があるため、
        # 先頭アーティストを代表として使用
        artist_name = artists[0]

        # ========================================
        # ① まずアーティストタグを確認
        # ========================================

        artist_tags = self.get_cached_artist_tags(
            artist_name
        )

        artist_mood_score = MoodScorer.score_tags(
            artist_tags
        )

        # アーティストタグだけで判定できれば採用
        if artist_mood_score is not None:
            return {
                **track,
                "mood_tags": artist_tags,
                "mood_score": artist_mood_score,
                "mood_tag_source": "artist",
            }

        # ========================================
        # ② アーティストタグで判定できない場合だけ
        #    曲タグを確認
        # ========================================

        track_tags = self.get_cached_track_tags(
            artist_name,
            track_name
        )

        track_mood_score = MoodScorer.score_tags(
            track_tags
        )

        # 曲タグで判定できれば採用
        if track_mood_score is not None:
            return {
                **track,
                "mood_tags": track_tags,
                "mood_score": track_mood_score,
                "mood_tag_source": "track",
            }

        # ========================================
        # ③ どちらでもmood判定できなかった
        # ========================================

        if artist_tags:
            tags = artist_tags
            tag_source = "artist"
        elif track_tags:
            tags = track_tags
            tag_source = "track"
        else:
            tags = []
            tag_source = None

        return {
            **track,
            "mood_tags": tags,
            "mood_score": None,
            "mood_tag_source": tag_source,
        }