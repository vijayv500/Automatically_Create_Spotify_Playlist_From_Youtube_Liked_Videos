import json
import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import requests
import youtube_dl

from spotify_info import spotify_user_id, spotify_token


class CreatePlaylist:

    def __init__(self):
        self.youtube_client = self.get_youtube_client()
        self.all_song_info = {}

    def get_youtube_client(self):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()

        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube_client

    def get_liked_videos(self):
        request = self.youtube_client.videos().list(
            part="snippet,contentDetails,statistics",
            myRating='like',
            maxResults=50)

        response = request.execute()

        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = f"https://www.youtube.com/watch?v={item['id']}"
            try:
                video = youtube_dl.YoutubeDL({}).extract_info(youtube_url, download=False)
            except:
                pass

            #             print(youtube_url)
            #             print()

            try:
                song_name = video["track"]
                artist = video["artist"]
            except KeyError:
                continue

            self.all_song_info[video_title] = {
                "youtube_url": youtube_url,
                "song_name": song_name,
                "artist": artist,
                "spotify_uri": self.get_spotify_uri(song_name, artist)
            }

    def create_playlist(self):

        request_body = json.dumps({
            "name": "From Youtube With Love",
            "description": "Liked music from Youtube",
            "public": True
        })

        query = f"https://api.spotify.com/v1/users/{spotify_user_id}/playlists"
        response = requests.post(
            query,
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {spotify_token}"
            }
        )
        response_json = response.json()

        return response_json["id"]

    def get_spotify_uri(self, song_name, artist):
        query = f"https://api.spotify.com/v1/search?query=track%3A{song_name}+artist%3A{artist}&type=track&offset=0&limit=20"
        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {spotify_token}"
            }
        )
        response_json = response.json()

        try:
            songs = response_json["tracks"]["items"]
            uri = songs[0]["uri"]
        except:
            uri = None

        return uri

    def add_song_to_playlist(self):

        self.get_liked_videos()

        uris = [info["spotify_uri"]
                for song, info in self.all_song_info.items()]

        uris = [i for i in uris if i != None]  # removes URIs with None value

        #         print(uris)

        playlist_id = self.create_playlist()

        # adds all songs into new playlist
        request_data = json.dumps(uris)

        query = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

        response = requests.post(
            query,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {spotify_token}"
            }
        )

        response_json = response.json()
        return response_json


if __name__ == '__main__':
    cp = CreatePlaylist()
    cp.add_song_to_playlist()
