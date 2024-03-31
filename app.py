import base64
import os
import requests
import uuid
from datetime import datetime, timedelta
from flask import Flask, redirect, request, url_for

from utils.sessions import store_session
from utils.spotify import get_queue

app = Flask(__name__)


@app.route("/auth")
def auth():
    state = uuid.uuid4()
    scope = "user-read-private user-read-email user-read-playback-state user-modify-playback-state"
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    callback_url = os.getenv("APP_URL") + "/callback"
    url = f"https://accounts.spotify.com/authorize?response_type=code&client_id={client_id}&scope={scope}&redirect_uri={callback_url}&state={state}"
    return redirect(url)


@app.route("/callback")
def auth_callback():
    code = request.args.get("code")
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    auth_key = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    callback_url = os.getenv("APP_URL") + "/callback"

    r = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "code": code,
            "redirect_uri": callback_url,
            "grant_type": "authorization_code",
        },
        headers={
            "Authorization": f"Basic {auth_key}",
        },
    )

    if "error" in r.text:
        print(r.text)
        return redirect(url_for("auth"))

    auth_resp = r.json()

    r = requests.get(
        "https://api.spotify.com/v1/me",
        headers={"Authorization": f"Bearer {auth_resp["access_token"]}"},
    )
    user_resp = r.json()
    username = user_resp["id"]

    store_session(username, auth_resp)

    return redirect(url_for('now_playing', username=username))


@app.route("/<string:username>/queue")
def now_playing(username):
    queue = get_queue(username)
    return queue


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
