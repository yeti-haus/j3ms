import base64
import requests
from datetime import datetime, timedelta

from .db import exec_query
from .env import APP_URL, CLIENT_ID, CLIENT_SECRET
from .sessions import get_auth_token, store_session


def send_auth_request(username, path):
    access_token = get_auth_token(username)
    r = requests.get(
        f"https://api.spotify.com/v1/me{path}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    return r.json()


def get_access_token(code=None, refresh_token=None):
    auth_key = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    if code:
        callback_url = APP_URL + "/callback"
        data = {
            "code": code,
            "redirect_uri": callback_url,
            "grant_type": "authorization_code",
        }
    elif refresh_token:
        data = {
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

    r = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {auth_key}",
        },
        data=data,
    )

    if "error" in r:
        print(r.text)
        return None
    return r.json()


def refresh_sessions():
    soon = datetime.now() + timedelta(minutes=60)
    rows_to_refresh = exec_query(
        f"SELECT username, refresh_token FROM sessions WHERE expires_at < '{soon}'"
    )

    for username, refresh_token in rows_to_refresh:
        print("Refreshing", username)
        get_access_token(refresh_token=refresh_token)
        store_session(username, get_access_token(refresh_token=refresh_token))


def simplify_queue_item(qi):
    # only process songs (for now)
    # https://developer.spotify.com/documentation/web-api/reference/get-queue
    if "show" in qi:
        return None

    return {
        "id": qi["id"],
        "name": qi["name"],
        "artists": ", ".join([v["name"] for v in qi["artists"]]),
        "link": qi["href"],
        "image": qi["album"]["images"][0]["url"],
    }


def get_queue(username):
    raw_queue = send_auth_request(username, "/player/queue")
    queue = []

    if "currently_playing" in raw_queue:
        queue.append(simplify_queue_item(raw_queue["currently_playing"]))

    for qi in raw_queue["queue"]:
        queue.append(simplify_queue_item(qi))

    return [v for v in queue if v]
