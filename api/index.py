from flask import Flask, request, jsonify, send_file, url_for
import yt_dlp
import tempfile
import os
import uuid
import imageio_ffmpeg

app = Flask(__name__)

# Temporary directory
TEMP_DIR = tempfile.mkdtemp(prefix="song_api_")

# File registry
files = {}


# ========================================
# FIND BUNDLED FFMPEG
# ========================================

try:
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

    if os.path.isfile(FFMPEG_PATH):
        FFMPEG_LOCATION = os.path.dirname(FFMPEG_PATH)
        FFMPEG_AVAILABLE = True
    else:
        FFMPEG_LOCATION = None
        FFMPEG_AVAILABLE = False

except Exception:
    FFMPEG_PATH = None
    FFMPEG_LOCATION = None
    FFMPEG_AVAILABLE = False


# ========================================
# HOME
# ========================================

@app.route("/")
def home():

    return jsonify({
        "status": "online",
        "ffmpeg": FFMPEG_AVAILABLE,
        "ffmpeg_path": FFMPEG_PATH if FFMPEG_AVAILABLE else None,
        "usage": "/song?name=SONG_NAME"
    })


# ========================================
# SONG
# ========================================

@app.route("/song")
def song():

    name = request.args.get("name", "").strip()

    if not name:
        return jsonify({
            "success": False,
            "error": "Missing name parameter",
            "example": "/song?name=Never Gonna Give You Up"
        }), 400

    if not FFMPEG_AVAILABLE:
        return jsonify({
            "success": False,
            "error": "FFmpeg not available"
        }), 500

    try:

        # ========================================
        # SEARCH
        # ========================================

        search_query = f"ytsearch5:{name}"

        search_options = {
            "quiet": True,
            "no_warnings": True
        }

        with yt_dlp.YoutubeDL(search_options) as ydl:

            info = ydl.extract_info(
                search_query,
                download=False
            )

        entries = info.get("entries") or []

        entries = [
            entry
            for entry in entries
            if entry and entry.get("id")
        ]

        if not entries:

            return jsonify({
                "success": False,
                "error": "Song not found",
                "query": name
            }), 404

        video = entries[0]

        video_id = video.get("id")
        title = video.get("title") or name

        if not video_id:

            return jsonify({
                "success": False,
                "error": "Video ID not found"
            }), 500

        # ========================================
        # THUMBNAILS
        # ========================================

        thumbnails = {
            "max": (
                f"https://i.ytimg.com/vi/"
                f"{video_id}/maxresdefault.jpg"
            ),
            "standard": (
                f"https://i.ytimg.com/vi/"
                f"{video_id}/sddefault.jpg"
            ),
            "high": (
                f"https://i.ytimg.com/vi/"
                f"{video_id}/hqdefault.jpg"
            ),
            "medium": (
                f"https://i.ytimg.com/vi/"
                f"{video_id}/mqdefault.jpg"
            )
        }

        thumbnail = thumbnails["max"]

        # ========================================
        # FILE ID
        # ========================================

        file_id = str(uuid.uuid4())

        output_template = os.path.join(
            TEMP_DIR,
            f"{file_id}.%(ext)s"
        )

        mp3_path = os.path.join(
            TEMP_DIR,
            f"{file_id}.mp3"
        )

        # ========================================
        # DOWNLOAD
        # ========================================

        options = {

            "format": "bestaudio/best",

            "outtmpl": output_template,

            "quiet": True,
            "no_warnings": True,

            # Exact FFmpeg executable
            "ffmpeg_location": FFMPEG_PATH,

            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320"
                }
            ]
        }

        video_url = (
            f"https://www.youtube.com/watch?v={video_id}"
        )

        with yt_dlp.YoutubeDL(options) as ydl:

            ydl.download([
                video_url
            ])

        # ========================================
        # FIND MP3
        # ========================================

        if not os.path.exists(mp3_path):

            possible = [
                os.path.join(TEMP_DIR, filename)
                for filename in os.listdir(TEMP_DIR)
                if filename.startswith(file_id)
                and filename.endswith(".mp3")
            ]

            if not possible:

                return jsonify({
                    "success": False,
                    "error": "MP3 generation failed"
                }), 500

            mp3_path = possible[0]

        # ========================================
        # SAVE
        # ========================================

        files[file_id] = mp3_path

        download_url = url_for(
            "download",
            file_id=file_id,
            _external=True
        )

        # ========================================
        # RESPONSE
        # ========================================

        return jsonify({

            "success": True,

            "title": title,

            "video_id": video_id,

            "thumbnail": thumbnail,

            "thumbnails": thumbnails,

            "quality": "320kbps MP3",

            "download_url": download_url

        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ========================================
# FILE
# ========================================

@app.route("/file/<file_id>")
def download(file_id):

    filepath = files.get(file_id)

    if not filepath:
        return jsonify({
            "success": False,
            "error": "File not found or expired"
        }), 404

    if not os.path.exists(filepath):

        return jsonify({
            "success": False,
            "error": "File expired"
        }), 404

    return send_file(
        filepath,
        as_attachment=True,
        download_name="song.mp3",
        mimetype="audio/mpeg"
    )


# ========================================
# LOCAL SERVER
# ========================================

if __name__ == "__main__":

    print("=" * 50)
    print("Song API")
    print("=" * 50)

    print(
        "FFmpeg:",
        FFMPEG_PATH if FFMPEG_AVAILABLE else "NOT FOUND"
    )

    print("=" * 50)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
