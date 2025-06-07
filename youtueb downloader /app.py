import os
import time
from flask import Flask, render_template, request, Response, stream_with_context, redirect, url_for, send_from_directory, flash
from yt_dlp import YoutubeDL, DownloadError

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # required for flashing messages

@app.route('/progress')
def progress():
    def generate():
        for i in range(101):
            yield f"data:{i}\n\n"
            time.sleep(0.1)
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

# Create download folders
AUDIO_FOLDER = "downloads/audio"
VIDEO_FOLDER = "downloads/videos"
os.makedirs(VIDEO_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        mode = request.form.get("mode")
        resolution = request.form.get("resolution")

        if not url:
            flash("❌ URL cannot be empty.")
            return redirect("/")

        try:
            if mode == "audio":
                output_path = os.path.join(AUDIO_FOLDER, '%(title)s.%(ext)s')
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'noplaylist': True,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'outtmpl': output_path,
                }
            elif mode == "video":
                output_path = os.path.join(VIDEO_FOLDER, '%(title)s.%(ext)s')
                format_string = f'bestvideo[height={resolution}]+bestaudio/best'
                ydl_opts = {
                    'format': format_string,
                    'noplaylist': True,
                    'merge_output_format': 'mp4',
                    'outtmpl': output_path,
                }
            else:
                flash("❌ Invalid mode selected.")
                return redirect("/")

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_filename = ydl.prepare_filename(info)
                downloaded_filename = os.path.basename(downloaded_filename)
                flash("✅ Download completed successfully!")
                return render_template("index.html", download_filename=downloaded_filename, mode=mode)

        except DownloadError:
            flash("❌ Failed to download. Please check the URL.")
            return redirect("/")
        except Exception as e:
            flash(f"❌ Error: {str(e)}")
            return redirect("/")

    return render_template("index.html")

@app.route('/download/<mode>/<path:filename>')
def download_file(mode, filename):
    folder = AUDIO_FOLDER if mode == "audio" else VIDEO_FOLDER
    return send_from_directory(folder, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
