import base64
import requests

from .env import APP_URL, CLIENT_ID, CLIENT_SECRET


def send_auth_request(username, path, method="get"):
    from .sessions import get_auth_token

    access_token = get_auth_token(username)
    if not access_token:
        return None

    url = f"https://api.spotify.com/v1/me{path}"
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
    raw_queue = send_auth_request(username, "/player/queue")
    if not raw_queue:
        return []
    queue = []

    if "currently_playing" in raw_queue:
        queue.append(simplify_queue_item(raw_queue["currently_playing"]))

    for qi in raw_queue["queue"]:
        queue.append(simplify_queue_item(qi))

    return [v for v in queue if v]
