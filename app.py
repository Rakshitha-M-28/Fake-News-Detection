from flask import Flask, render_template, request, redirect, session
import json
import os
import random
from google import genai   # ✅ NEW SDK

app = Flask(__name__)
app.secret_key = "secret123"

# 🔐 Gemini API
client = genai.Client(api_key="AIzaSyA4M3Hi6ybYzx1vULn72iqnT4vIUchQO5E")

# 📂 Files
USER_FILE = "users.json"
HISTORY_FILE = "history.json"

# ✅ Create JSON files if not exist
for file in [USER_FILE, HISTORY_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)

# ---------------- LANDING ----------------
@app.route("/")
def landing():
    return render_template("landing.html")

# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        otp = str(random.randint(1000, 9999))

        session["temp_user"] = {
            "username": username,
            "password": password,
            "otp": otp
        }

        return render_template("signup.html", otp=otp)

    return render_template("signup.html")

# ---------------- VERIFY OTP ----------------
@app.route("/verify_signup", methods=["POST"])
def verify_signup():
    entered_otp = request.form["otp"]
    temp = session.get("temp_user")

    if temp and entered_otp == temp["otp"]:

        with open(USER_FILE, "r") as f:
            users = json.load(f)

        users[temp["username"]] = temp["password"]

        with open(USER_FILE, "w") as f:
            json.dump(users, f, indent=4)

        session.pop("temp_user", None)
        return redirect("/signin")

    return "❌ Invalid OTP"

# ---------------- SIGNIN ----------------
@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with open(USER_FILE, "r") as f:
            users = json.load(f)

        if username in users and users[username] == password:
            session["user"] = username
            return redirect("/home")

        return "❌ Invalid Username or Password"

    return render_template("signin.html")

# ---------------- HOME ----------------
@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/signin")

    username = session["user"]

    with open(HISTORY_FILE, "r") as f:
        history_data = json.load(f)

    history = history_data.get(username, [])

    return render_template("index.html", history=history)

# ---------------- PREDICT ----------------
@app.route("/predict", methods=["POST"])
def predict():
    if "user" not in session:
        return redirect("/signin")

    news = request.form["news"]

    prompt = f"""
Classify the news as REAL or FAKE.
Also give a short explanation.

News:
{news}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",   # ✅ valid model
            contents=prompt
        )

        result = response.text

    except Exception as e:
        result = f"Error: {str(e)}"

    username = session["user"]

    # 📜 Save history
    with open(HISTORY_FILE, "r") as f:
        history_data = json.load(f)

    if username not in history_data:
        history_data[username] = []

    history_data[username].append({
        "news": news,
        "result": result
    })

    with open(HISTORY_FILE, "w") as f:
        json.dump(history_data, f, indent=4)

    return redirect("/home")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)