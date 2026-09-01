class MusicLibrary:

    def __init__(self, spotify_service, favorite_playlist_id):
        self.spotify_service = spotify_service
        self.favorite_playlist_id = favorite_playlist_id

    def get_favorite_tracks(self):
        if not self.favorite_playlist_id:
            raise ValueError(
                "FAVORITEプレイリストIDが設定されていません。"
            )

        return self.spotify_service.get_playlist_tracks(
            self.favorite_playlist_id,
            limit=50
        )

    def get_favorite_artists(self):
        tracks = self.get_favorite_tracks()

        artists = []
        seen = set()

        for track in tracks:
            for artist_name in track["artists"]:
                normalized_name = artist_name.casefold()

                if normalized_name in seen:
                    continue

                seen.add(normalized_name)
                artists.append(artist_name)

        return artists