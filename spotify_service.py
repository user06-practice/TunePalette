import spotipy

class SpotifyApiSchemaError(Exception):
    """Spotify APIのレスポンス形式が想定と異なる場合のエラー"""
    pass

class SpotifyService:

    def __init__(self, auth_manager):
        self.spotify = spotipy.Spotify(auth_manager=auth_manager)

    def get_top_tracks(self, limit=10, time_range="medium_term"):
        results = self.spotify.current_user_top_tracks(
            limit=limit,
            time_range=time_range
        )

        tracks = []

        for track in results["items"]:
            tracks.append(self._normalize_track(track))

        return tracks

    def get_playlists(self, limit=50):
        results = self.spotify.current_user_playlists(limit=limit)

        playlists = []

        for playlist in results["items"]:
            playlists.append({
                "id": playlist["id"],
                "name": playlist["name"]
            })

        return playlists

    def get_playlist_tracks(self, playlist_id, limit=50):
        tracks = []
        offset = 0

        while True:
            results = self.spotify.playlist_items(
                playlist_id,
                limit=limit,
                offset=offset,
                additional_types=("track",)
            )

            playlist_items = results["items"]

            for playlist_item in playlist_items:

                # 2026年以降の仕様では "item"
                # 旧仕様では "track"
                if "item" in playlist_item:
                    track = playlist_item["item"]

                elif "track" in playlist_item:
                    track = playlist_item["track"]

                else:
                    raise SpotifyApiSchemaError(
                        "Spotify playlist itemに 'item' または 'track' がありません。"
                        "Spotify APIの仕様変更を確認してください。"
                    )

                if track is None:
                    continue

                tracks.append(self._normalize_track(track))

            # 取得件数がlimit未満なら、これが最後のページ
            if len(playlist_items) < limit:
                break

            offset += limit

        return tracks

        tracks = []

        for playlist_item in results["items"]:

            # 2026年2月以降のSpotify APIでは "item"
            # 旧仕様では "track" だったため、両方に対応しておく
            if "item" in playlist_item:
                track = playlist_item["item"]

            elif "track" in playlist_item:
                track = playlist_item["track"]

            else:
                raise SpotifyApiSchemaError(
                    "Spotify playlist itemに 'item' または 'track' がありません。"
                    "Spotify APIの仕様変更を確認してください。"
                )

            if track is None:
                continue

            tracks.append(self._normalize_track(track))

        return tracks

    def get_current_account(self):
        user = self.spotify.current_user()

        account_id = user.get("account_id")

        if not account_id:
            raise SpotifyApiSchemaError(
                "Spotifyユーザー情報に 'account_id' がありません。"
                "Spotify APIの仕様変更を確認してください。"
            )

        return {
            "account_id": account_id,
            "display_name": user.get("display_name", "")
        }

    @staticmethod
    def _normalize_track(track):
        return {
            "id": track.get("id"),
            "name": track.get("name", ""),
            "artists": [
                artist.get("name", "")
                for artist in track.get("artists", [])
            ],
            "uri": track.get("uri")
        }