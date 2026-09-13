
from flask import Flask, request, jsonify, send_file, url_for
import yt_dlp
import tempfile
import os
import uuid
import shutil

app = Flask(__name__)

# Temporary storage
TEMP_DIR = tempfile.mkdtemp(prefix="song_api_")
files = {}


def find_ffmpeg():
    # Check PATH
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")

    if ffmpeg and ffprobe:
        return os.path.dirname(ffmpeg)

    # Windows
    windows_paths = [
        r"C:\ffmpeg\bin",
        r"C:\Program Files\ffmpeg\bin",
        r"C:\Program Files (x86)\ffmpeg\bin",
    ]

    for path in windows_paths:
        if (
            os.path.isfile(os.path.join(path, "ffmpeg.exe"))
            and os.path.isfile(os.path.join(path, "ffprobe.exe"))
        ):
            return path

    # Linux / Termux
    linux_paths = [
        "/data/data/com.termux/files/usr/bin",
        "/usr/bin",
        "/usr/local/bin",
        "/bin",
    ]

    for path in linux_paths:
        if (
            os.path.isfile(os.path.join(path, "ffmpeg"))
            and os.path.isfile(os.path.join(path, "ffprobe"))
        ):
            return path

    return None


FFMPEG_LOCATION = find_ffmpeg()


@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "ffmpeg": bool(FFMPEG_LOCATION),
        "usage": "/song?name=SONG_NAME"
    })


@app.route("/song")
def song():

    name = request.args.get("name", "").strip()

    if not name:
        return jsonify({
            "success": False,
            "error": "Missing name parameter",
            "example": "/song?name=Never Gonna Give You Up"
        }), 400

    # Check FFmpeg
    if not FFMPEG_LOCATION:
        return jsonify({
            "success": False,
            "error": "FFmpeg not found",
            "message": "Install FFmpeg and ffprobe first."
        }), 500

    try:

        # ========================================
        # SEARCH YOUTUBE
        # ========================================

        search_query = f"ytsearch5:{name}"

        search_options = {
            "quiet": True,
            "no_warnings": True
        }

        # Do NOT use extract_flat
        # This allows yt-dlp to return metadata.
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

        # First valid result
        video = entries[0]

        video_id = video.get("id")
        title = video.get("title") or name

        if not video_id:
            return jsonify({
                "success": False,
                "error": "YouTube video ID not found"
            }), 500

        # ========================================
        # HIGH QUALITY THUMBNAIL
        # ========================================

        # Maximum quality thumbnail
        thumbnail = (
            f"https://i.ytimg.com/vi/"
            f"{video_id}/maxresdefault.jpg"
        )

        # Additional thumbnail URLs
        thumbnails = {
            "max": f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
            "standard": f"https://i.ytimg.com/vi/{video_id}/sddefault.jpg",
            "high": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
            "medium": f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"
        }

        # ========================================
        # CREATE UNIQUE FILE
        # ========================================

        file_id = str(uuid.uuid4())

        filepath = os.path.join(
            TEMP_DIR,
            f"{file_id}.mp3"
        )

        # ========================================
        # DOWNLOAD AUDIO
        # ========================================

        download_options = {

            "format": "bestaudio/best",

            "outtmpl": os.path.join(
                TEMP_DIR,
                f"{file_id}.%(ext)s"
            ),

            "quiet": True,
            "no_warnings": True,

            # FFmpeg path
            "ffmpeg_location": FFMPEG_LOCATION,

            # Convert to MP3
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",

                    # 320 kbps
                    "preferredquality": "320"
                }
            ]
        }

        video_url = (
            f"https://www.youtube.com/watch?v={video_id}"
        )

        with yt_dlp.YoutubeDL(download_options) as ydl:
            ydl.download([video_url])

        # ========================================
        # CHECK MP3
        # ========================================

        if not os.path.exists(filepath):

            possible_files = [
                os.path.join(TEMP_DIR, filename)
                for filename in os.listdir(TEMP_DIR)
                if filename.startswith(file_id)
                and filename.lower().endswith(".mp3")
            ]

            if not possible_files:
                return jsonify({
                    "success": False,
                    "error": "MP3 generation failed"
                }), 500

            filepath = possible_files[0]

        # ========================================
        # SAVE FILE
        # ========================================

        files[file_id] = filepath

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


@app.route("/file/<file_id>")
def download(file_id):

    filepath = files.get(file_id)

    if not filepath or not os.path.exists(filepath):

        return jsonify({
            "success": False,
            "error": "File not found or expired"
        }), 404

    return send_file(
        filepath,
        as_attachment=True,
        download_name="song.mp3",
        mimetype="audio/mpeg"
    )


if __name__ == "__main__":

    print("=" * 50)
    print("Song API")
    print("=" * 50)

    if FFMPEG_LOCATION:
        print("FFmpeg:", FFMPEG_LOCATION)
    else:
        print("WARNING: FFmpeg NOT FOUND")

    print("Audio: MP3 320kbps")
    print("Thumbnail: Maximum available")
    print("Server: http://127.0.0.1:5000")

    print("=" * 50)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
