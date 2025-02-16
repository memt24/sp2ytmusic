# Spotify to YouTube Music Playlist Converter

This project is a Flask-based web application that transfers your playlists from Spotify to YouTube Music. It uses OAuth for secure authentication on both platforms and leverages the [ytmusicapi](https://github.com/sigma67/ytmusicapi) library for YouTube Music operations.

## Features

- **Spotify OAuth Authentication:** Sign in with your Spotify account to retrieve your playlists.
- **YouTube Music OAuth Setup:** Authorize and create playlists on your YouTube Music account.
- **Playlist Retrieval:** Fetch playlists and their tracks from Spotify.
- **Playlist Conversion:** Search for tracks on YouTube Music and create corresponding playlists.
- **Flask Web Interface:** Manage authentication and conversion processes through a simple web interface.

## Prerequisites

- Python 3.7 or later
- A Spotify Developer account with a registered application (to obtain `CLIENT_ID`, `CLIENT_SECRET`, and set `REDIRECT_URI`)
- A Google Developer account for YouTube Music API (to obtain `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, and set `YT_REDIRECT_URI`)
- [ytmusicapi](https://github.com/sigma67/ytmusicapi) dependency

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/<your-username>/<your-repo-name>.git
   cd <your-repo-name>
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. **Install the required dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** in the project root directory with your credentials:

   ```dotenv
   # Flask configuration
   FLASK_SESSION_KEY=your_flask_session_secret

   # Spotify API credentials
   CLIENT_ID=your_spotify_client_id
   CLIENT_SECRET=your_spotify_client_secret
   REDIRECT_URI=http://localhost:8888/callback

   # YouTube Music API credentials
   YT_CLIENT_ID=your_youtube_client_id
   YT_CLIENT_SECRET=your_youtube_client_secret

## Usage

### 1. YouTube Music OAuth Setup

Before starting the Flask application, you may need to run the OAuth setup for YouTube Music. This process uses your environment variables (or prompts for them if they are missing). Run the following command:

```bash
python api.py execute
```

This simulates the CLI call for the `ytmusicapi` OAuth setup, configuring your YouTube Music authentication with the provided credentials.

### 2. Start the Flask Application

After the OAuth setup is complete (or if it was already configured), start the Flask server:

```bash
python api.py
```

Open your browser and navigate to [http://localhost:8888/](http://localhost:8888/) to access the application.

### Application Endpoints

- **Home:** `/`  
  A welcome page with a link to begin the Spotify login process.

- **Spotify Login:** `/login`  
  Redirects to Spotify's OAuth page for authentication.

- **Spotify Callback:** `/callback`  
  Handles the Spotify OAuth callback and retrieves the access token.

- **User Info:** `/get_user_info`  
  Retrieves your Spotify user information and redirects to playlist retrieval.

- **Playlists:** `/get_playlists`  
  Fetches your Spotify playlists and stores them in the session.

- **Playlist Tracks:** `/get_playlist_tracks`  
  Processes tracks from each playlist.

- **Create Playlists on YouTube Music:** `/create_playlists`  
  Searches for tracks on YouTube Music and creates new playlists based on your Spotify playlists using the `ytmusicapi`.

## Notes

- Ensure your `.env` file contains the correct credentials for both Spotify and YouTube Music.
- The YouTube Music OAuth setup is integrated using the `ytmusicapi` setup script. This setup flow is triggered by running `python api.py execute`.
- Flask sessions are used to temporarily store playlist and track data during processing.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests if you have suggestions or improvements.

