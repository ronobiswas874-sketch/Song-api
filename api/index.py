from flask import Flask, request, jsonify, send_file
import yt_dlp
import imageio_ffmpeg
import tempfile
import os
import uuid

app = Flask(__name__)

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

COOKIE_FILE = os.path.join(
    BASE_DIR,
    "cookies.txt"
)

COOKIES_AVAILABLE = os.path.isfile(
    COOKIE_FILE
)

TEMP_DIR = tempfile.gettempdir()

FILES = {}


# ========================================
# FFMPEG
# ========================================

try:
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
    FFMPEG_AVAILABLE = os.path.isfile(
        FFMPEG_PATH
    )
except Exception:
    FFMPEG_PATH = None
    FFMPEG_AVAILABLE = False


# ========================================
# COOKIE OPTIONS
# ========================================

def cookie_options():

    if COOKIES_AVAILABLE:
        return {
            "cookiefile": COOKIE_FILE
        }

    return {}


# ========================================
# HOME
# ========================================

@app.route("/")
def home():

    return jsonify({
        "status": "online",
        "ffmpeg": FFMPEG_AVAILABLE,
        "cookies": COOKIES_AVAILABLE,
        "usage": "/song?name=SONG_NAME"
    })


# ========================================
# SONG
# ========================================

@app.route("/song")
def song():

    name = request.args.get(
        "name",
        ""
    ).strip()

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

        search_options = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True
        }

        search_options.update(
            cookie_options()
        )

        query = f"ytsearch5:{name}"

        with yt_dlp.YoutubeDL(
            search_options
        ) as ydl:

            info = ydl.extract_info(
                query,
                download=False
            )


        entries = info.get(
            "entries"
        ) or []

        entries = [
            x for x in entries
            if x and x.get("id")
        ]


        if not entries:

            return jsonify({
                "success": False,
                "error": "Song not found",
                "query": name
            }), 404


        video = entries[0]

        video_id = video.get(
            "id"
        )

        title = video.get(
            "title"
        ) or name


        # ========================================
        # THUMBNAILS
        # ========================================

        thumbnails = {

            "max":
                f"https://i.ytimg.com/vi/"
                f"{video_id}/maxresdefault.jpg",

            "standard":
                f"https://i.ytimg.com/vi/"
                f"{video_id}/sddefault.jpg",

            "high":
                f"https://i.ytimg.com/vi/"
                f"{video_id}/hqdefault.jpg",

            "medium":
                f"https://i.ytimg.com/vi/"
                f"{video_id}/mqdefault.jpg"
        }


        # ========================================
        # FILE ID
        # ========================================

        file_id = str(
            uuid.uuid4()
        )

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

            "noplaylist": True,

            "ffmpeg_location":
                FFMPEG_PATH,

            "postprocessors": [
                {
                    "key":
                        "FFmpegExtractAudio",

                    "preferredcodec":
                        "mp3",

                    "preferredquality":
                        "320"
                }
            ]
        }

        options.update(
            cookie_options()
        )


        video_url = (
            "https://www.youtube.com/watch?v="
            + video_id
        )


        with yt_dlp.YoutubeDL(
            options
        ) as ydl:

            ydl.download([
                video_url
            ])


        # ========================================
        # FIND MP3
        # ========================================

        if not os.path.exists(
            mp3_path
        ):

            possible = [

                os.path.join(
                    TEMP_DIR,
                    filename
                )

                for filename in os.listdir(
                    TEMP_DIR
                )

                if (
                    filename.startswith(file_id)
                    and filename.endswith(".mp3")
                )
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

        FILES[file_id] = mp3_path


        # ========================================
        # RESPONSE
        # ========================================

        return jsonify({

            "success": True,

            "title": title,

            "video_id": video_id,

            "thumbnail":
                thumbnails["max"],

            "thumbnails":
                thumbnails,

            "quality":
                "320kbps MP3",

            "download_url":
                f"/file/{file_id}"
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

    filepath = FILES.get(
        file_id
    )


    if not filepath:

        return jsonify({

            "success": False,

            "error":
                "File not found or expired"

        }), 404


    if not os.path.exists(
        filepath
    ):

        FILES.pop(
            file_id,
            None
        )

        return jsonify({

            "success": False,

            "error":
                "File expired"

        }), 404


    return send_file(

        filepath,

        as_attachment=True,

        download_name="song.mp3",

        mimetype="audio/mpeg"
    )


# ========================================
# VERCEL
# ========================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )
