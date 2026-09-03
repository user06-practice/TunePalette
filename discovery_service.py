import random


class DiscoveryService:

    def __init__(
            self,
            music_library,
            lastfm_service,
            spotify_service
    ):
        self.music_library = music_library
        self.lastfm_service = lastfm_service
        self.spotify_service = spotify_service

    def get_candidate_artists(
        self,
        seed_limit=5,
        similar_limit=10,
        rng=None
    ):
        if seed_limit <= 0:
            raise ValueError(
                "seed_limitは1以上で指定してください。"
            )

        if similar_limit <= 0:
            raise ValueError(
                "similar_limitは1以上で指定してください。"
            )

        if rng is None:
            rng = random.Random()

        favorite_artists = (
            self.music_library.get_favorite_artists()
        )

        if not favorite_artists:
            return []

        # FAVORITEから今回の探索起点をランダムに選ぶ
        seed_count = min(
            seed_limit,
            len(favorite_artists)
        )

        seed_artists = rng.sample(
            favorite_artists,
            seed_count
        )

        candidates = {}

        for seed_artist in seed_artists:

            similar_artists = (
                self.lastfm_service.get_similar_artists(
                    seed_artist,
                    limit=similar_limit
                )
            )

            for artist in similar_artists:
                artist_name = artist["name"]
                similarity = artist["similarity"]

                normalized_name = artist_name.casefold()

                if normalized_name not in candidates:
                    candidates[normalized_name] = {
                        "name": artist_name,
                        "similarity": similarity,
                        "source_artists": [
                            seed_artist
                        ],
                    }

                else:
                    candidate = candidates[
                        normalized_name
                    ]

                    # 複数の起点から出た場合は
                    # 最も高い類似度を残す
                    candidate["similarity"] = max(
                        candidate["similarity"],
                        similarity
                    )

                    candidate["source_artists"].append(
                        seed_artist
                    )

        return list(candidates.values())

    def get_candidate_tracks(
            self,
            candidate_artists,
            artist_limit=10,
            tracks_per_artist=10
    ):
        if artist_limit <= 0:
            raise ValueError(
                "artist_limitは1以上で指定してください。"
            )

        if not 1 <= tracks_per_artist <= 10:
            raise ValueError(
                "tracks_per_artistは1～10で指定してください。"
            )

        favorite_tracks = (
            self.music_library.get_favorite_tracks()
        )

        favorite_track_ids = {
            track["id"]
            for track in favorite_tracks
            if track.get("id")
        }

        # 今回は類似度の高いアーティストから検索
        selected_artists = sorted(
            candidate_artists,
            key=lambda artist: artist["similarity"],
            reverse=True
        )[:artist_limit]

        candidate_tracks = []
        seen_track_ids = set()
        seen_track_keys = set()

        for candidate_artist in selected_artists:
            artist_name = candidate_artist["name"]

            tracks = (
                self.spotify_service.search_tracks_by_artist(
                    artist_name,
                    limit=tracks_per_artist
                )
            )

            for track in tracks:
                track_id = track.get("id")

                if not track_id:
                    continue

                # FAVORITEに登録済みの曲はDISCOVEREDにしない
                if track_id in favorite_track_ids:
                    continue

                # 複数の検索結果から同じ曲が出た場合も1回だけ
                if track_id in seen_track_ids:
                    continue

                # Spotify検索結果に対象アーティスト本人が
                # 含まれていることも確認する
                track_artists = {
                    name.casefold()
                    for name in track["artists"]
                }

                if artist_name.casefold() not in track_artists:
                    continue

                track_name = track.get("name")

                if not track_name:
                    continue

                normalized_artists = tuple(
                    sorted(
                        name.strip().casefold()
                        for name in track["artists"]
                        if name
                    )
                )

                track_key = (
                    track_name.strip().casefold(),
                    normalized_artists
                )

                # Spotify IDが違っても、
                # 曲名＋アーティストが同じなら同一曲として除外
                if track_key in seen_track_keys:
                    continue

                seen_track_ids.add(track_id)
                seen_track_keys.add(track_key)

                candidate_tracks.append({
                    **track,
                    "discovery_artist": artist_name,
                    "similarity": candidate_artist["similarity"],
                    "source_artists": candidate_artist[
                        "source_artists"
                    ],
                })

        return candidate_tracks

