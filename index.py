# ============================================================
# IMPORTS & INITIALIZATION
# ============================================================

import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

def search_song_via_itunes(query):
    try:
        formatted_query = query.replace(" ", "+")
        Url = f"https://itunes.apple.com/search?term={formatted_query}&entity=song&limit=1"
        
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(Url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return None
            
        data = response.json()
        results = data.get("results", [])
        
        if not results:
            return None
            
        song = results[0]
        title = song.get("trackName", "Unknown Title")
        artist = song.get("artistName", "Unknown Artist")
        duration_ms = song.get("trackTimeMillis", 180000)
        duration_sec = int(duration_ms / 1000)
        
        audio_url = song.get("previewUrl", "")
        
        # গানের অফিশিয়াল লোগো/আর্টওয়ার্ক লিংক সংগ্রহ করা এবং হাই রেজুলেশন করা
        artwork_url = song.get("artworkUrl100", "")
        if artwork_url:
            artwork_url = artwork_url.replace("100x100bb", "600x600bb")
        
        if audio_url:
            return {
                "title": f"{title} - {artist}",
                "duration": duration_sec,
                "audio_url": audio_url,
                "logo_url": artwork_url
            }
            
    except Exception as e:
        print(f"iTunes API Error: {e}")
        return None
        
    return None


@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "service": "ITunes Music API Server with Logo is Running"
    }), 200


@app.route("/health")
def health():
    return jsonify({
        "status": "online",
        "health": "OK"
    }), 200


# 👉 Music Search API (/search?name=)
@app.route("/search", methods=["GET"])
def search_music_api():
    query = request.args.get("name", "").strip()

    if not query:
        return jsonify({
            "error": "Please provide a song name using ?name=your_song_name"
        }), 400

    song_data = search_song_via_itunes(query)
    
    if not song_data:
        return jsonify({
            "status": "error",
            "message": "No songs found for this query."
        }), 404

    return jsonify({
        "status": "success",
        "query": query,
        "title": song_data["title"],
        "duration": song_data["duration"],
        "logo_url": song_data["logo_url"],
        "audio_url": song_data["audio_url"]
    }), 200


# 👉 Tumble API (/tumble?songname=)
@app.route("/tumble", methods=["GET"])
def tumble_music_api():
    query = request.args.get("songname", "").strip()

    if not query:
        return jsonify({
            "error": "Please provide a song name using ?songname=your_song_name"
        }), 400

    song_data = search_song_via_itunes(query)
    
    if not song_data:
        return jsonify({
            "status": "error",
            "message": "No songs found for this query."
        }), 404

    return jsonify({
        "status": "success",
        "endpoint": "tumble",
        "songname": query,
        "title": song_data["title"],
        "duration": song_data["duration"],
        "logo_url": song_data["logo_url"],
        "audio_url": song_data["audio_url"]
    }), 200


# ============================================================
# MAIN RUNNER
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "3000"))
    app.run(
        host="0.0.0.0",
        port=port
    )
