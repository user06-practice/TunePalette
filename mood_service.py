from mood_scorer import MoodScorer


class MoodService:

    def __init__(self, lastfm_service):
        self.lastfm_service = lastfm_service

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

        # Spotifyでは複数アーティストの場合があるが、
        # Last.fm検索では先頭アーティストを代表として使用
        artist_name = artists[0]

        # ========================================
        # ① まず曲そのもののタグを取得
        # ========================================

        tags = self.lastfm_service.get_track_top_tags(
            artist_name,
            track_name
        )

        tag_source = "track"

        # ========================================
        # ② 曲タグがない場合
        #    アーティストタグへフォールバック
        # ========================================

        if not tags:

            tags = self.lastfm_service.get_artist_top_tags(
                artist_name,
                limit=10
            )

            tag_source = "artist"

        # ========================================
        # ③ どちらからも取得できなかった場合
        # ========================================

        if not tags:

            return {
                **track,
                "mood_tags": [],
                "mood_score": None,
                "mood_tag_source": None,
            }

        # ========================================
        # ④ タグからmood_scoreを計算
        # ========================================

        mood_score = MoodScorer.score_tags(
            tags
        )

        return {
            **track,
            "mood_tags": tags,
            "mood_score": mood_score,
            "mood_tag_source": tag_source,
        }