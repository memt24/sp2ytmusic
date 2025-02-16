import os
import requests
import urllib.parse
import json
import time
from flask import Flask, request, session, redirect, url_for, jsonify
from flask_session import Session
import base64
from datetime import datetime, timedelta
from ytmusicapi.setup import main
import dotenv
import sys
import argparse



# Load environment variables from .env file
dotenv.load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SESSION_KEY", "default_secret_key")

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1'

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8888/callback")


yt_client_id = os.getenv("YT_CLIENT_ID")
yt_client_secret = os.getenv("YT_CLIENT_SECRET")
YT_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
YT_TOKEN_URL = "https://oauth2.googleapis.com/token"

scope = 'playlist-read-private playlist-read-collaborative'


@app.route('/')
def home():
    return "hello<a href='/login'>login</a>"


@app.route('/login', methods=['GET'])
def login():
    params = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': scope,
        'show_dialog': False
    }

    # Directly redirect to Spotify's auth URL
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)


@app.route('/callback', methods=['GET'])
def callback():
    # Check for error in callback
    if 'error' in request.args:
        return jsonify({'error': request.args['error']})

    # Get the authorization code
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'No authorization code provided'})

    # Create Basic Authorization header
    auth_header = base64.b64encode(
        f"{client_id}:{client_secret}".encode()
    ).decode()

    headers = {
        'Authorization': f'Basic {auth_header}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }

    try:
        response = requests.post(TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()

        token_data = response.json()
        access_token = token_data['access_token']
        expires_in = token_data['expires_in']
        refresh_token = token_data['refresh_token']
        return redirect(
            url_for('get_user_info', access_token=access_token, refresh_token=refresh_token, expires_in=expires_in,
                    auth_header=auth_header
                    ))

    except requests.exceptions.RequestException as e:
        return jsonify({
            'error': 'Failed to get token',
            'details': str(e),
            'status_code': response.status_code if 'response' in locals() else None
        }), 500


@app.route('/get_user_info', methods=['GET', 'POST'])
def get_user_info():
    current_timestamp = datetime.now().timestamp()
    expires_in = float(request.args.get('expires_in', 0))
    expiration_time = current_timestamp + expires_in

    if current_timestamp > expiration_time:
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': request.args.get('refresh_token')
        }
        headers = {
            'Authorization': f'Basic {request.args.get("auth_header")}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        response = requests.post(TOKEN_URL, headers=headers, data=req_body)
        token_data = response.json()
        access_token = token_data['access_token']
    else:
        access_token = request.args.get('access_token')
        if not access_token:
            return jsonify({'error': 'No access token provided'}), 401

    api_url = API_BASE_URL + "/me"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.get(api_url, headers=headers)

    user_data = response.json()

    return redirect(url_for('get_playlists', access_token=access_token, user_id=user_data['id']))


class playlist:
    def __init__(self, name, description, pic, id, public):
        self.id = id
        self.name = name
        self.description = description
        self.pic = pic
        self.public = public

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'pic': self.pic,
            'public': self.public
        }


@app.route('/get_playlists', methods=['GET', 'POST'])
def get_playlists():
    user_id = request.args.get('user_id')
    access_token = request.args.get('access_token')

    if not user_id or not access_token:
        return jsonify({"error": "Missing user_id or access_token"}), 400

    api_url = f"{API_BASE_URL}/users/{user_id}/playlists"
    headers = {"Authorization": f"Bearer {access_token}"}
    all_playlists = []
    offset = 0
    limit = 50

    try:
        while True:
            response = requests.get(api_url, headers=headers, params={"offset": offset, "limit": limit})
            response.raise_for_status()
            playlists_data = response.json()

            if not isinstance(playlists_data.get('items'), list):
                print("Stopping pagination: No items list found")
                break

            for item in playlists_data['items']:
                playlist_id = item.get('id')
                if playlist_id:
                    images = item.get('images', [])
                    cover_image = images[0].get('url') if images else None
                    check_public = item.get('public')
                    pl = playlist(
                        name=item.get('name'),
                        description=item.get('description'),
                        pic=cover_image,
                        id=playlist_id,
                        public='public' if check_public else 'private'
                    )
                    all_playlists.append(pl)
                    print(f"Playlist {len(all_playlists)}: {pl.id} - {pl.name}")

            if len(playlists_data.get('items', [])) < limit:
                print("Reached end of playlists")
                break
            offset += limit

        session['all_playlists'] = [pl.to_dict() for pl in all_playlists]
        session.modified = True

        print("\n=== ALL PLAYLISTS ===")
        print(f"Total playlists: {len(all_playlists)}")
        for pl in all_playlists:
            print(f"- {pl.id}: {pl.name}")

        return redirect(url_for('get_playlist_tracks',
                                total=len(all_playlists),
                                access_token=access_token))

    except requests.exceptions.RequestException as e:
        print(f"\n=== ERROR ===")
        print(f"Request failed: {str(e)}")
        print(f"Response text: {e.response.text if e.response else 'No response'}")
        return jsonify({"error": f"API request failed: {str(e)}"}), 500


@app.route('/get_playlist_tracks', methods=['GET', 'POST'])
def get_playlist_tracks():
    access_token = request.args.get('access_token')

    if not access_token:
        return jsonify({"error": "Missing access_token"}), 400

    all_tracks = []
    print("\n=== STARTING TRACK PROCESSING ===")

    playlists = session.get('all_playlists', [])

    for pl in playlists:
        playlist_id = pl.get('id')
        if not playlist_id:
            continue

        try:
            print(f"\n🔍 Processing playlist: {pl.get('name')} ({playlist_id})")
            api_url = f"{API_BASE_URL}/playlists/{playlist_id}/tracks"
            headers = {'Authorization': f'Bearer {access_token}'}

            playlist_tracks = []
            offset = 0
            total_tracks = 0

            while True:
                params = {
                    'limit': 100,
                    'offset': offset,
                    'additional_types': 'track'
                }
                response = requests.get(api_url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()
                items = data.get('items', [])
                total_tracks += len(items)

                for item in items:
                    track = item.get('track')
                    if not track or track.get('is_local'):
                        continue

                    track_info = {
                        'name': track.get('name', 'Unknown Track'),
                        'artist': track.get('artists', [{}])[0].get('name', 'Unknown Artist'),
                        'album': track.get('album', {}).get('name', 'Unknown Album'),
                        'duration_ms': track.get('duration_ms', 0),
                        'uri': track.get('uri'),
                        'playlist_id': playlist_id
                    }

                    playlist_tracks.append(track_info)
                    print(f"🎵 {track_info['artist']} - {track_info['name']}")

                if data.get('next'):
                    offset += 100
                else:
                    print(f"✅ Finished processing playlist: {pl.get('name')}")
                    print(f"📊 Total tracks found: {total_tracks}")
                    break

            session[playlist_id] = playlist_tracks
            all_tracks.extend(playlist_tracks)

        except requests.exceptions.RequestException as e:
            print(f"\n❌ Error processing playlist {pl.get('name')}: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response content: {e.response.text[:200]}...")
            continue

    session['total_tracks'] = all_tracks
    session.modified = True

    print("\n=== PROCESSING COMPLETE ===")
    print(f"🎉 Total tracks stored: {len(all_tracks)}")

    return ("<a href='/create_playlists'>create_playlists</a>")


def chunk_list(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


@app.route('/create_playlists')
def create_playlists():
    ytmusic = YTMusic(
        'oauth.json',
        oauth_credentials=OAuthCredentials(
            client_id=yt_client_id,
            client_secret=yt_client_secret
        )
    )

    for pl in session['all_playlists']:
        yt_playlist_track_ids = []
        playlist_tracks = session.get(pl['id'], [])

        for track in playlist_tracks:
            q = f"{track['name']} {track['artist']}"
            track_info = ytmusic.search(query=q, filter='songs', ignore_spelling=False)

            if not track_info:
                print(f"[WARN] No search results found for: {q}")
                continue

            song_id = track_info[0].get('videoId')
            if not song_id:
                print(f"[WARN] Search result for '{q}' did not contain a 'videoId'.")
                continue

            yt_playlist_track_ids.append(song_id)
            print(f"[INFO] Found '{track['name']}' with video id: {song_id}")

        created_response = ytmusic.create_playlist(
            title=pl['name'],
            description=pl['description'],
            privacy_status='PRIVATE'
        )
        print(f"[DEBUG] create_playlist response: {created_response}")

        if isinstance(created_response, dict):
            playlist_id = created_response.get('playlistId', None)
        else:
            playlist_id = created_response

        if not playlist_id:
            print(f"[ERROR] Failed to obtain a valid playlist ID for {pl['name']}")
            continue

        time.sleep(3)

        for chunk in chunk_list(yt_playlist_track_ids, 10):
            add_result = ytmusic.add_playlist_items(
                playlistId=playlist_id,
                videoIds=chunk,
                duplicates=True
            )
            print(f"[DEBUG] add_playlist_items result for playlist '{pl['name']}' (chunk): {add_result}")
            time.sleep(1)

        print(f"[INFO] Created and updated playlist: {pl['name']}")

    return jsonify({'message': 'Playlist creation process completed'})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("execute", help="Type 'execute' to run ytmusicapi oauth")
    args = parser.parse_args()
    
    try:
        if args.execute == "execute":
            # If credentials are not set via environment variables, prompt the user.
            if not yt_client_id or not yt_client_secret:
                yt_client_id = input("Enter your Google Youtube API client ID: ")
                yt_client_secret = input("Enter your Google Youtube API client secret: ")
            
            # Simulate CLI arguments for the OAuth setup
            sys.argv = [
                'setup.py', 'oauth',
                '--client-id', yt_client_id,
                '--client-secret', yt_client_secret
            ]
            main()
        else:
            raise Exception("Invalid argument")
    except Exception as e:
        print(e)

    app.run(host='localhost', port=8888, debug=True)