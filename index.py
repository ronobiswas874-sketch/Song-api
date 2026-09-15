# ============================================================
# IMPORTS & INITIALIZATION
# ============================================================

import os
import yt_dlp
from flask import Flask, jsonify, request

# ============================================================
# FLASK SERVER & MUSIC API (/search?name= & /tumble?songname=)
# ============================================================

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "service": "Music API Server is Running"
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

    search_query = query if query.startswith("http://") or query.startswith("https://") else f"ytsearch1:{query}"

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=False)
            
            if 'entries' in info:
                info = info['entries'][0]

            title = info.get('title', 'Unknown Title')
            duration = info.get('duration', 0)
            
            audio_url = info.get('url')
            if not audio_url and 'formats' in info:
                for f in info['formats']:
                    if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                        audio_url = f.get('url')
                        break
            
            if not audio_url:
                audio_url = info.get('webpage_url', '')

            return jsonify({
                "status": "success",
                "query": query,
                "title": title,
                "duration": duration,
                "audio_url": audio_url
            }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# 👉 New Tumble API (/tumble?songname=)
@app.route("/tumble", methods=["GET"])
def tumble_music_api():
    query = request.args.get("songname", "").strip()

    if not query:
        return jsonify({
            "error": "Please provide a song name using ?songname=your_song_name"
        }), 400

    search_query = query if query.startswith("http://") or query.startswith("https://") else f"ytsearch1:{query}"

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=False)
            
            if 'entries' in info:
                info = info['entries'][0]

            title = info.get('title', 'Unknown Title')
            duration = info.get('duration', 0)
            
            audio_url = info.get('url')
            if not audio_url and 'formats' in info:
                for f in info['formats']:
                    if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                        audio_url = f.get('url')
                        break
            
            if not audio_url:
                audio_url = info.get('webpage_url', '')

            return jsonify({
                "status": "success",
                "endpoint": "tumble",
                "songname": query,
                "title": title,
                "duration": duration,
                "audio_url": audio_url
            }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ============================================================
# MAIN RUNNER
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "3000"))
    app.run(
        host="0.0.0.0",
        port=port
    )
