
from flask import Flask, request, jsonify, send_file
import yt_dlp
import imageio_ffmpeg
import tempfile
import os
import uuid

app = Flask(__name__)



cookies = """# Netscape HTTP Cookie File

.youtube.com	TRUE	/	TRUE	2147483647	HSID	A-RZoA72nMlelvNzL
.youtube.com	TRUE	/	TRUE	2147483647	SSID	A21KRqK752LYEiMFy
.youtube.com	TRUE	/	TRUE	2147483647	APISID	EZ85xpe41cowvSrz/AX_9vzpejTS_K7BYh
.youtube.com	TRUE	/	TRUE	2147483647	SAPISID	q6PFRPGMwnRJi-6V/AYyuv5b77dWEedRFJ
.youtube.com	TRUE	/	TRUE	2147483647	__Secure-1PAPISID	q6PFRPGMwnRJi-6V/AYyuv5b77dWEedRFJ
.youtube.com	TRUE	/	TRUE	2147483647	__Secure-3PAPISID	q6PFRPGMwnRJi-6V/AYyuv5b77dWEedRFJ
.youtube.com	TRUE	/	TRUE	2147483647	SID	g.a000CgngnNHfk_EtVgmnbQ56lG47TLIOHDe3l9c5BiQD83HcjCsW8fx0P09vwAnmoXqabCUi_wACgYKAYYSARYSFQHGX2MiNUewaSuVt4hpgAJAyMgC6hoVAUF8yKrEyyjDmEK7IdtbQ1SWA0n60076
.youtube.com	TRUE	/	TRUE	2147483647	__Secure-1PSID	g.a000CgngnNHfk_EtVgmnbQ56lG47TLIOHDe3l9c5BiQD83HcjCsWSdqoBI6Nr7I5UGNRDWAzwgACgYKAZkSARYSFQHGX2MinPo_tK9X7Jro3dpWFtL0HBoVAUF8yKoQJu22KHtUQGS8AqKkXQ900076
.youtube.com	TRUE	/	TRUE	2147483647	__Secure-3PSID	g.a000CgngnNHfk_EtVgmnbQ56lG47TLIOHDe3l9c5BiQD83HcjCsW3XLuS1JQkL8AqjsQawZVjAACgYKAfwSARYSFQHGX2MinzVRFOJZypjNAMWPwDgqkhoVAUF8yKpnI2Lf-Bow3aBzTgF_9zVR0076
.youtube.com	TRUE	/	TRUE	2147483647	__Secure-YNID	21.YT=LH7QFVPK9oV6UVybjQYjMqPeg8OctWMKFQdI4hK7naBI0b6Yu8jcjVa1sQL0kZhB2BfavKWX1MRAXOipB-_ENniAgWszmaaygySd7yr7Ia3oigfvFnVNJ51QUnv-JqMmH9yp7kvXGhUZKMpwup6JrDLCZu2PkrFgBVtnWIAf2UygUmRJVN3fUkWt43x8KPtYiU11phdqPob70U-nRC8-AuwfzSd-3w1Wl4NOjzr9j3NJTgyP7REU-gsIpieskFZpKREpd4SLWiZLjb5l8ucBfMXD0OCL_elcbwvWcUA_D3Y5f6tHOo0wdYc_VpBBXo60SUvZcybdn7kh9Z7Dd0udZQ
.youtube.com	TRUE	/	TRUE	2147483647	YSC	HKHpx4IGTvU
.youtube.com	TRUE	/	TRUE	2147483647	VISITOR_INFO1_LIVE	Kre3ZnD3s7Y
.youtube.com	TRUE	/	TRUE	2147483647	VISITOR_PRIVACY_METADATA	CgJJThIEGgAgQg%3D%3D
.youtube.com	TRUE	/	TRUE	2147483647	PREF	tz=Asia.Calcutta
.youtube.com	TRUE	/	TRUE	2147483647	__Secure-1PSIDTS	sidts-CjUBXMw41bEhacfI8L5kdSPrhhe1uQfrt7970FHf-9T8nDz5qcDJmRjweXUKDrS1iSz5skyrLRAA
.youtube.com	TRUE	/	TRUE	2147483647	__Secure-3PSIDTS	sidts-CjUBXMw41bEhacfI8L5kdSPrhhe1uQfrt7970FHf-9T8nDz5qcDJmRjweXUKDrS1iSz5skyrLRAA
.youtube.com	TRUE	/	TRUE	2147483647	__Secure-ROLLOUT_TOKEN	COfx8P37gpPQehD9v8nczuqWAxj6nrSTz-qWAw%3D%3D
.youtube.com	TRUE	/	TRUE	2147483647	SIDCC	AKEyXzUXEYKPk3K9-lj1ZgpLeIbSGG7te2Bjd9I67vn6dhPztXXVCVFquAmzgRnkp2chgFed
.youtube.com	TRUE	/	TRUE	2147483647	__Secure-1PSIDCC	AKEyXzWb4XQB1Y4dctoehQwhTaaYDSS4wg_MFs1l_x3EjKOhc9Elp3YR8q98JZcHcKJsiQTBRA
.youtube.com	TRUE	/	TRUE	2147483647	__Secure-3PSIDCC	AKEyXzV8u7Gq92h6mqrfM7YfLKydAeGaO590qFk-hr-C6dbdHJiYTo2hARDD1lnJ1o69OGf_KA"""


# ========================================
# TEMP DIRECTORY
# ========================================

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

def get_cookie_options():

    if not cookies.strip():
        return {}

    return {
        "cookiefile": create_cookie_file()
    }


# ========================================
# CREATE TEMP COOKIE FILE
# ========================================

def create_cookie_file():

    cookie_path = os.path.join(
        TEMP_DIR,
        "yt_cookies.txt"
    )

    with open(
        cookie_path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(cookies)

    return cookie_path


# ========================================
# HOME
# ========================================

@app.route("/")
def home():

    return jsonify({

        "status": "online",

        "ffmpeg":
            FFMPEG_AVAILABLE,

        "cookies":
            bool(cookies.strip()),

        "usage":
            "/song?name=SONG_NAME"
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

            "error":
                "Missing name parameter",

            "example":
                "/song?name=Never Gonna Give You Up"

        }), 400


    if not FFMPEG_AVAILABLE:

        return jsonify({

            "success": False,

            "error":
                "FFmpeg not available"

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
            get_cookie_options()
        )


        search_query = (
            f"ytsearch5:{name}"
        )


        with yt_dlp.YoutubeDL(
            search_options
        ) as ydl:

            info = ydl.extract_info(
                search_query,
                download=False
            )


        entries = (
            info.get("entries")
            or []
        )


        entries = [

            entry

            for entry in entries

            if entry
            and entry.get("id")
        ]


        if not entries:

            return jsonify({

                "success": False,

                "error":
                    "Song not found",

                "query":
                    name

            }), 404


        video = entries[0]


        video_id = video.get(
            "id"
        )


        title = video.get(
            "title"
        ) or name


        if not video_id:

            return jsonify({

                "success": False,

                "error":
                    "Video ID not found"

            }), 500


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
        # DOWNLOAD OPTIONS
        # ========================================

        options = {

            "format":
                "bestaudio/best",

            "outtmpl":
                output_template,

            "quiet":
                True,

            "no_warnings":
                True,

            "noplaylist":
                True,

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
            get_cookie_options()
        )


        # ========================================
        # VIDEO URL
        # ========================================

        video_url = (

            "https://www.youtube.com/watch?v="

            + video_id
        )


        # ========================================
        # DOWNLOAD
        # ========================================

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

                for filename
                in os.listdir(TEMP_DIR)

                if (

                    filename.startswith(
                        file_id
                    )

                    and

                    filename.endswith(
                        ".mp3"
                    )
                )
            ]


            if not possible:

                return jsonify({

                    "success":
                        False,

                    "error":
                        "MP3 generation failed"

                }), 500


            mp3_path = possible[0]


        # ========================================
        # REGISTER FILE
        # ========================================

        FILES[file_id] = mp3_path


        # ========================================
        # RESPONSE
        # ========================================

        return jsonify({

            "success":
                True,

            "title":
                title,

            "video_id":
                video_id,

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

            "success":
                False,

            "error":
                str(e)

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

            "success":
                False,

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

            "success":
                False,

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
