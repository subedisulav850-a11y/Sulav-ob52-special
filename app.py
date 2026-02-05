from flask import Flask, render_template, request, redirect, session
import os
import subprocess
import zipfile
import json

# ---------------- APP SETUP ----------------
app = Flask(__name__)
app.secret_key = "CHANGE_THIS_SECRET"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- LOAD USERS ----------------
with open("users.json", "r") as f:
    USERS = json.load(f)

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if username in USERS and USERS[username] == password:
            session["user"] = username
            return redirect("/dashboard")

        return "❌ Wrong username or password"

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    bots = os.listdir(UPLOAD_FOLDER)
    return render_template("dashboard.html", bots=bots)

# ---------------- UPLOAD ----------------
@app.route("/upload", methods=["POST"])
def upload():
    if "user" not in session:
        return redirect("/")

    file = request.files.get("file")
    if not file or file.filename == "":
        return "❌ No file selected"

    filename = file.filename.replace(" ", "_")
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)

    # ZIP → EXTRACT
    if filename.endswith(".zip"):
        extract_folder = save_path.replace(".zip", "")
        os.makedirs(extract_folder, exist_ok=True)

        with zipfile.ZipFile(save_path, "r") as zip_ref:
            zip_ref.extractall(extract_folder)

        os.remove(save_path)

    return redirect("/dashboard")

# ---------------- START BOT ----------------
@app.route("/start/<botname>")
def start_bot(botname):
    if "user" not in session:
        return redirect("/")

    bot_path = os.path.join(UPLOAD_FOLDER, botname)

    # SINGLE PY FILE
    if botname.endswith(".py") and os.path.isfile(bot_path):
        subprocess.Popen(["python3", bot_path])
        return redirect("/dashboard")

    # FOLDER BOT
    if os.path.isdir(bot_path):
        for f in os.listdir(bot_path):
            if f.endswith(".py"):
                subprocess.Popen(["python3", f], cwd=bot_path)
                return redirect("/dashboard")

        return "❌ No .py file found in folder"

    return "❌ Invalid bot"

# ---------------- STOP BOT ----------------
@app.route("/stop/<botname>")
def stop_bot(botname):
    if "user" not in session:
        return redirect("/")

    os.system(f"pkill -f {botname}")
    return redirect("/dashboard")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)