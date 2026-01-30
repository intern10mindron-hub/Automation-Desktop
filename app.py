from flask import Flask, render_template, request, redirect, url_for
import datetime
import threading
import time
import os
import json
import subprocess
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "audio"
ALLOWED_EXTENSIONS = {"mp3"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

TASK_FILE = "tasks.json"

arti_process = None
hanuman_process = None
current_mode = None 
manual_process = None
tts_process = None
manual_audio = None
scheduled_process = None

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------- TASK STORAGE ----------------

def load_tasks():
    if os.path.exists(TASK_FILE):
        with open(TASK_FILE, "r") as f:
            return json.load(f)
    return []

def save_tasks(tasks):
    with open(TASK_FILE, "w") as f:
        json.dump(tasks, f, indent=4)

scheduled_tasks = load_tasks()

def get_next_id():
    return max([t["id"] for t in scheduled_tasks], default=0) + 1

def play_arti():
    global arti_process
    if arti_process is None or arti_process.poll() is not None:
        arti_process = subprocess.Popen(
            [ "cvlc",
              "--play-and-exit",
              "--extraintf", "http",
              "--http-password", "1234",
              "audio/arti.mp3"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("🔊 Arti started")

def play_hanuman():
    global hanuman_process
    if hanuman_process is None or hanuman_process.poll() is not None:
        hanuman_process = subprocess.Popen(
            ["cvlc",
             "--play-and-exit",
             "--extraintf", "http",
             "--http-password", "1234",
             "audio/hanuman_chalisa.mp3"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("🔊 Hanuman Chalisa started")


def stop_arti():
    global arti_process, hanuman_process, scheduled_process # Add scheduled_process here

    if arti_process and arti_process.poll() is None:
        arti_process.terminate()
        arti_process = None
        print("⏹ Arti stopped")

    if hanuman_process and hanuman_process.poll() is None:
        hanuman_process.terminate()
        hanuman_process = None
        print("⏹ Hanuman Chalisa stopped")

    # ✅ ADD THIS: Stop the custom scheduled audio
    if scheduled_process and scheduled_process.poll() is None:
        scheduled_process.terminate()
        scheduled_process = None
        print("⏹ Scheduled custom audio stopped")

def stop_all_audio():
    stop_arti()


def set_volume(delta):
    # Get current volume
    os.system(
        f'curl -s "http://:1234@localhost:8080/requests/status.xml?command=volume&val={delta}" > /dev/null'
    )

def volume_up():
    if arti_process and arti_process.poll() is None:
        arti_process.stdin.write("volup 20\n")
        arti_process.stdin.flush()

    if hanuman_process and hanuman_process.poll() is None:
        hanuman_process.stdin.write("volup 20\n")
        hanuman_process.stdin.flush()


def volume_down():
    if arti_process and arti_process.poll() is None:
        arti_process.stdin.write("voldown 20\n")
        arti_process.stdin.flush()

    if hanuman_process and hanuman_process.poll() is None:
        hanuman_process.stdin.write("voldown 20\n")
        hanuman_process.stdin.flush()


# ---------------- TIME PARSER ----------------


def parse_time_to_24h(time_str):
    time_str = time_str.strip().upper()
    try:
        if "AM" in time_str or "PM" in time_str:
            return datetime.datetime.strptime(time_str, "%I:%M %p").strftime("%H:%M")
        else:
            return datetime.datetime.strptime(time_str, "%H:%M").strftime("%H:%M")
    except:
        return None
    

# ---------------- COMMAND PARSER ----------------


def parse_and_add_task(command_text):
    if not command_text:
        return

    parts = command_text.strip().split()
    if len(parts) < 2:
        return

    time_24 = parse_time_to_24h(parts[0])
    if not time_24:
        return

    action = " ".join(parts[1:]).lower()

    scheduled_tasks.append({
        "id": get_next_id(),
        "time": time_24,
        "action": action,
        "repeat": "daily",
        "last_run": ""
    })

    save_tasks(scheduled_tasks)
    print("✅ Task added:", time_24, action)

def clean_finished_processes():
    global arti_process, hanuman_process, manual_process, tts_process, current_mode

    for p in [arti_process, hanuman_process, manual_process, tts_process]:
        if p and p.poll() is not None:
            p = None

    # If nothing is running → free system
    if not any([
        arti_process and arti_process.poll() is None,
        hanuman_process and hanuman_process.poll() is None,
        manual_process and manual_process.poll() is None,
        tts_process and tts_process.poll() is None,
    ]):
        current_mode = None 

# ---------------- SCHEDULER ----------------

def scheduler():
    global current_mode, tts_process, scheduled_process
    print("⏰ Scheduler started")

    while True:
        clean_finished_processes()

        now = datetime.datetime.now()
        today = now.strftime("%Y-%m-%d")

        for task in scheduled_tasks:
            # Only daily tasks & not already run today
            if task["repeat"] == "daily" and task["last_run"] != today:

                task_time = datetime.datetime.strptime(task["time"], "%H:%M").time()
                task_dt = datetime.datetime.combine(now.date(), task_time)
                diff = (now - task_dt).total_seconds()

                # Run task if within 1 minute window
                if 0 <= diff <= 60:
                    # 🔥 Schedule ALWAYS has priority
                    stop_all_audio()

                    if tts_process:
                        tts_process.terminate()

                    current_mode = "schedule"

                    action = task["action"].lower().strip()

                    # 🔊 Built-in audios
                    if action == "play arti":
                        play_arti()

                    elif action == "play hanuman chalisa":
                        play_hanuman()

                    elif action.startswith("play "):
                        audio_name = action.replace("play ", "").strip()
                        if not audio_name.endswith(".mp3"):
                            audio_name += ".mp3"

                        audio_path = f"audio/{audio_name}"

                        if os.path.exists(audio_path):
                            scheduled_process = subprocess.Popen(
                                [
                                    "cvlc",
                                    "--play-and-exit",
                                    "--extraintf", "http",
                                    "--http-password", "1234",
                                    audio_path
                                ],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                            )
                        else:
                            print("❌ Audio not found:", audio_path)

                    # Mark task as executed today
                    task["last_run"] = today
                    save_tasks(scheduled_tasks)

        time.sleep(5)


# ---------------- ROUTES ----------------


@app.route("/")
def home():
    return render_template("index.html", tasks=scheduled_tasks)

@app.route("/command", methods=["POST"])
def command():
    parse_and_add_task(request.form.get("command"))
    return redirect(url_for("home"))

@app.route("/upload", methods=["POST"])
def upload_audio():
    if "file" not in request.files:
        return redirect(url_for("home"))

    file = request.files["file"]

    if file.filename == "":
        return redirect(url_for("home"))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    return redirect(url_for("home"))


@app.route("/remove/<int:task_id>")
def remove_task(task_id):
    global scheduled_tasks
    scheduled_tasks = [t for t in scheduled_tasks if t["id"] != task_id]
    save_tasks(scheduled_tasks)
    return redirect(url_for("home"))

@app.route("/stop_arti")
def stop_arti_route():
    stop_arti()
    return redirect(url_for("home"))

@app.route("/play/<audio>")
def play_audio(audio):
    if audio == "arti":
        play_arti()
    elif audio == "hanuman":
        play_hanuman()
    return redirect(url_for("home"))


@app.route("/stop_all")
def stop_all():
    stop_all_audio()
    return redirect(url_for("home"))


@app.route("/volume_up")
def volume_up_route():
    set_volume("+20")
    return redirect(url_for("home"))


@app.route("/volume_down")
def volume_down_route():
    set_volume("-20")
    return redirect(url_for("home"))

@app.route("/set_volume/<int:value>")
def set_volume_route(value):
    os.system(
        f'curl -s "http://:1234@localhost:8080/requests/status.xml?command=volume&val={value}" > /dev/null'
    )
    return ("", 204)

@app.route("/manual/audios")
def list_audios():
    files = [f for f in os.listdir("audio") if f.endswith(".mp3")]
    return {"audios": files}

@app.route("/manual/toggle/<audio>")
def manual_toggle(audio):
    global manual_process, manual_audio, current_mode

    current_mode = "manual"

    # Pause if same audio is playing
    if manual_audio == audio and manual_process and manual_process.poll() is None:
        manual_process.terminate()
        manual_process = None
        manual_audio = None
        return ("", 204)

    # Stop previous audio
    if manual_process and manual_process.poll() is None:
        manual_process.terminate()

    manual_audio = audio
    manual_process = subprocess.Popen(
    [
        "cvlc",
        "--loop",
        "--extraintf", "http",
        "--http-password", "1234",
        f"audio/{audio}"
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

    return ("", 204)

@app.route("/manual/stop")
def manual_stop():
    global manual_process, manual_audio, current_mode

    if manual_process:
        manual_process.terminate()

    manual_process = None
    manual_audio = None
    current_mode = None
    return ("", 204)

@app.route("/tts", methods=["POST"])
def text_to_speech():
    global tts_process, current_mode

    text = request.form.get("text")
    if not text:
        return ("", 204)

    # Stop everything else
    stop_all_audio()
    if tts_process:
        tts_process.terminate()

    current_mode = "manual"

    # Speak text
    tts_process = subprocess.Popen(
        ["espeak-ng", text],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return ("", 204) 


# ---------------- MAIN ----------------

if __name__ == "__main__":
    threading.Thread(target=scheduler, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)