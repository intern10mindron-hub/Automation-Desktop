# 🎵 Raspberry Pi Audio Automation Dashboard (Flask + VLC)

A Flask-based web dashboard for Raspberry Pi that allows you to play, schedule, stop, and control audio reliably using VLC.

This project supports:
- Manual audio playback
- Scheduled (daily) audio playback
- Text-to-Speech (TTS)
- Reliable STOP functionality
- Volume control via VLC HTTP interface
- Custom MP3 uploads

Designed for real-life automation use cases.

---

## 🚀 Features

- Flask web interface
- Manual audio player
- Daily scheduled audio tasks
- Text-to-Speech playback
- Proper STOP button (no stuck audio)
- VLC (`cvlc`) based playback
- Volume control support
- Works on Raspberry Pi OS (Pi 4 / Pi 5)

---

## 🧠 How It Works

Each audio source runs in its **own VLC process** using `subprocess.Popen`.

The app:
- Tracks running VLC processes globally
- Stops the correct process when STOP is pressed
- Prevents parallel audio playback
- Gives scheduler the highest priority

This avoids common issues like:
- Audio not stopping
- Multiple audios playing together
- Volume control breaking

---

## 📁 Project Structure

audio-automation/
│
├── app.py
├── tasks.json
├── audio/
│ ├── arti.mp3
│ ├── hanuman.mp3
│ └── uploaded_audio.mp3
│
├── templates/
│ └── index.html
│
├── static/
│ └── style.css
│
└── README.md

yaml
Copy code

---

## ⚙️ Requirements

### Hardware
- Raspberry Pi (Pi 4 / Pi 5 recommended)
- Speaker / amplifier

### Software
- Python 3.9+
- VLC

Install dependencies:
```bash
sudo apt update
sudo apt install vlc curl -y
pip install flask
▶️ Run the Project
bash
Copy code
python3 app.py
Open in browser:

cpp
Copy code
http://<raspberry-pi-ip>:5000
⏰ Scheduler
Tasks stored in tasks.json

Supports daily repeat

Scheduler checks every 5 seconds

Runs task within a 1-minute window

Stops any running audio before starting new one

Example task:

json
Copy code
{
  "time": "06:00",
  "action": "play arti",
  "repeat": "daily",
  "last_run": ""
}
🗣 Text-to-Speech (TTS)
Enter text in web UI

Audio plays immediately

Stops manual or scheduled audio before playing

TTS process is tracked and terminated correctly

⏹ STOP Button (Important)
STOP button stops:

Arti

Hanuman Chalisa

Scheduled uploaded MP3

TTS audio

This works because the app:

Stores the running VLC process globally

Terminates the correct process directly

No pkill hacks are required.

🔊 Volume Control
Uses VLC HTTP interface:

bash
Copy code
http://localhost:8080/requests/status.xml
Allows:

Volume up / down

Mute / unmute

Without restarting audio

🛡 Why This Project Is Reliable
No zombie VLC processes

No parallel playback

No random audio stopping

Proper process ownership

Tested for real-life automation

📌 Use Cases
Temple / religious automation

Home audio automation

Office announcements

Raspberry Pi media controller

Flask + system automation learning

👩‍💻 Author
Khushi
Python Developer | Raspberry Pi Automation
Built with patience, debugging, and real fixes

yaml
Copy code

---

If you want next:
- 📸 screenshots section
- 🛠 systemd service setup
- 📦 GitHub release version
- 🧪 debug/FAQ section

Just tell me.
