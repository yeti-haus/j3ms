import base64
import requests

from .db import exec_query
from .env import APP_URL, CLIENT_ID, CLIENT_SECRET


def send_auth_request(username, path, method="get"):
    from .sessions import get_auth_token

    access_token = get_auth_token(username)
    if not access_token:
        return None

    url = f"https://api.spotify.com{path}"
    headers = {"Authorization": f"Bearer {access_token}"}

    if method == "post":
        r = requests.post(url, headers=headers)
        if r.status_code >= 400:
            raise ValueError(r.text)
    else:
        r = requests.get(url, headers=headers)
        try:
            return r.json()
        except Exception as e:
            print(r.text)
            raise e


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


def simplify_queue_item(qi):
    # only process songs (for now)
    # https://developer.spotify.com/documentation/web-api/reference/get-queue
    if not qi or "show" in qi:
        return None

    return {
        "id": qi["id"],
        "name": qi["name"],
        "artists": ", ".join([v["name"] for v in qi["artists"]]),
        "link": qi["href"],
        "image": qi["album"]["images"][0]["url"],
    }


def get_queue(username):
    raw_queue = send_auth_request(username, "/v1/me/player/queue")
    if not raw_queue or "queue" not in raw_queue:
        return []
    queue = []

    if "currently_playing" in raw_queue:
        queue.append(simplify_queue_item(raw_queue["currently_playing"]))

    for qi in raw_queue["queue"]:
        queue.append(simplify_queue_item(qi))

    valid = [v for v in queue if v]
    track_ids = [v["id"] for v in valid]
    added = exec_query(f"SELECT track_id, dj FROM queue_adds WHERE username = '{username}' AND track_id IN ('{"','".join(track_ids)}') AND timestamp > NOW() - INTERVAL '6 HOUR' ORDER BY timestamp ASC")
    for (track_id, dj) in added:
        for v in valid:
            if v["id"] == track_id:
                (dj_type, dj_id) = dj.split(':')
                v["dj"] = dj_id
                if dj_type == "fname":
                    v["dj_link"] = f"https://warpcast.com/{dj_id}"
    
    return valid


def attribute_track_addition(username, track_id, dj):
    exec_query(
        """
        INSERT INTO queue_adds (timestamp, username, track_id, dj)
        VALUES (NOW(), %s, %s, %s)
        """,
        (username, track_id, dj),
    )
