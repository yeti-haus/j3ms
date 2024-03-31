import base64
import requests
import uuid
from flask import Flask, redirect, request, url_for

from utils.env import APP_URL, CLIENT_ID, CLIENT_SECRET
from utils.sessions import store_session
from utils.spotify import get_queue, get_access_token, refresh_sessions

app = Flask(__name__)


@app.route("/auth")
def auth():
    state = uuid.uuid4()
    scope = "user-read-private user-read-email user-read-playback-state user-modify-playback-state"
    callback_url = APP_URL + "/callback"
    url = f"https://accounts.spotify.com/authorize?response_type=code&client_id={CLIENT_ID}&scope={scope}&redirect_uri={callback_url}&state={state}"
    return redirect(url)


@app.route("/auth/refresh")
def auth_refresh():
    refresh_sessions()
    return "success"


@app.route("/callback")
def auth_callback():
    code = request.args.get("code")
    auth_resp = get_access_token(code=code)
    if not auth_resp:
        return redirect(url_for("auth"))

    r = requests.get(
        "https://api.spotify.com/v1/me",
        headers={"Authorization": f"Bearer {auth_resp['access_token']}"},
    )
    user_resp = r.json()
    username = user_resp["id"]

    store_session(username, auth_resp)

    return redirect(url_for("now_playing", username=username))


@app.route("/<string:username>/queue")
def now_playing(username):
    queue = get_queue(username)
    return queue


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
