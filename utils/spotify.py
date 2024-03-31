import requests

from .sessions import get_auth_token


def send_auth_request(username, path):
    access_token = get_auth_token(username)

    r = requests.get(
        f"https://api.spotify.com/v1/me{path}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    return r.json()


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
