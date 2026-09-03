import requests


class LastfmApiSchemaError(Exception):
    """Last.fm APIのレスポンス形式が想定と異なる場合のエラー"""
    pass


class LastfmService:

    API_URL = "https://ws.audioscrobbler.com/2.0/"

    def __init__(self, api_key):
        self.api_key = api_key

    def get_similar_artists(self, artist_name, limit=10):
        params = {
            "method": "artist.getsimilar",
            "artist": artist_name,
            "api_key": self.api_key,
            "format": "json",
            "limit": limit,
            "autocorrect": 1,
        }

        response = requests.get(
            self.API_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if "similarartists" not in data:
            raise LastfmApiSchemaError(
                "Last.fmレスポンスに 'similarartists' がありません。"
                "APIエラーまたは仕様変更を確認してください。"
            )

        similarartists = data["similarartists"]

        if "artist" not in similarartists:
            raise LastfmApiSchemaError(
                "Last.fmレスポンスに 'artist' がありません。"
                "API仕様変更を確認してください。"
            )

        artists = []

        for artist in similarartists["artist"]:
            if "name" not in artist or "match" not in artist:
                raise LastfmApiSchemaError(
                    "Last.fm artistに 'name' または 'match' がありません。"
                    "API仕様変更を確認してください。"
                )

            artists.append({
                "name": artist["name"],
                "similarity": float(artist["match"]),
            })

        return artists

    def get_track_top_tags(
            self,
            artist_name,
            track_name
    ):
        if not artist_name:
            raise ValueError(
                "artist_nameを指定してください。"
            )

        if not track_name:
            raise ValueError(
                "track_nameを指定してください。"
            )

        params = {
            "method": "track.gettoptags",
            "artist": artist_name,
            "track": track_name,
            "api_key": self.api_key,
            "format": "json",
            "autocorrect": 1,
        }

        response = requests.get(
            self.API_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        # Last.fmが通常レスポンスではなく
        # APIエラーを返した場合
        if "error" in data:
            error_code = data.get("error")
            error_message = data.get(
                "message",
                ""
            )

            # 一時障害・対象なし・レート制限などは
            # TunePalette全体を停止せず、
            # このアーティストだけタグなしとして扱う
            recoverable_errors = {
                7,  # Invalid resource
                8,  # Operation failed
                11,  # Service offline
                16,  # Temporary error
                29,  # Rate limit exceeded
            }

            if error_code in recoverable_errors:
                print(
                    f"Last.fm artistタグ取得をスキップ: "
                    f"{error_code} {error_message}"
                )

                return []

            # APIキー不正など、
            # 設定ミスの可能性があるものはエラーにする
            raise LastfmApiSchemaError(
                f"Last.fm APIエラー: "
                f"{error_code} {error_message}"
            )

        if "toptags" not in data:
            raise LastfmApiSchemaError(
                "Last.fmレスポンスに 'toptags' がありません。"
                "APIエラーまたは仕様変更を確認してください。"
            )

        if "tag" not in data["toptags"]:
            raise LastfmApiSchemaError(
                "Last.fmレスポンスの toptags に "
                "'tag' がありません。"
                "API仕様変更を確認してください。"
            )

        tags = []

        for tag in data["toptags"]["tag"]:
            if "name" not in tag:
                raise LastfmApiSchemaError(
                    "Last.fm tagに 'name' がありません。"
                    "API仕様変更を確認してください。"
                )

            tags.append(
                tag["name"]
            )

        return tags

    def get_artist_top_tags(
            self,
            artist_name
    ):
        if not artist_name:
            raise ValueError(
                "artist_nameを指定してください。"
            )

        params = {
            "method": "artist.gettoptags",
            "artist": artist_name,
            "api_key": self.api_key,
            "format": "json",
            "autocorrect": 1,
        }

        response = requests.get(
            self.API_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        # Last.fmが通常レスポンスではなく
        # APIエラーを返した場合
        if "error" in data:
            error_code = data.get("error")
            error_message = data.get(
                "message",
                ""
            )

            # 一時障害・対象なし・レート制限などは
            # TunePalette全体を停止せず、
            # このアーティストだけタグなしとして扱う
            recoverable_errors = {
                7,  # Invalid resource
                8,  # Operation failed
                11,  # Service offline
                16,  # Temporary error
                29,  # Rate limit exceeded
            }

            if error_code in recoverable_errors:
                print(
                    f"Last.fm artistタグ取得をスキップ: "
                    f"{error_code} {error_message}"
                )

                return []

            # APIキー不正など、
            # 設定ミスの可能性があるものはエラーにする
            raise LastfmApiSchemaError(
                f"Last.fm APIエラー: "
                f"{error_code} {error_message}"
            )

        if "toptags" not in data:
            raise LastfmApiSchemaError(
                "Last.fmレスポンスに 'toptags' がありません。"
                "APIエラーまたは仕様変更を確認してください。"
            )

        if "tag" not in data["toptags"]:
            raise LastfmApiSchemaError(
                "Last.fmレスポンスの toptags に "
                "'tag' がありません。"
                "API仕様変更を確認してください。"
            )

        tags = []

        for tag in data["toptags"]["tag"]:
            if "name" not in tag:
                raise LastfmApiSchemaError(
                    "Last.fm tagに 'name' がありません。"
                    "API仕様変更を確認してください。"
                )

            tags.append(
                tag["name"]
            )



        return tags