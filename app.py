import requests
import uuid
from flask import Flask, redirect, request, url_for, render_template

from utils.env import APP_URL, CLIENT_ID
from utils.farcaster import get_fname_from_fid
from utils.frames import generate_frame_for_queue_item
from utils.sessions import store_session, refresh_sessions
from utils.spotify import (
    attribute_track_addition,
    get_queue,
    get_access_token,
    send_auth_request,
    simplify_queue_item,
)

app = Flask(__name__)


# https://open.spotify.com/track/52ZQTzXbbWjS4kjOcV3z5b
@app.after_request
def add_cache_control_header(resp):
    resp.headers["Cache-Control"] = "max-age=60"
    return resp


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


@app.route("/<string:username>", methods=["GET", "POST"])
def now_playing(username):
    try:
        queue = get_queue(username)
        if not queue:
            return render_template("queue.html")

        raw_add = request.form.get("spotify_uri")
        fname = None
        try:
            if not raw_add:
                raw_add = request.json["untrustedData"]["inputText"]
                fid = request.json["untrustedData"]["fid"]
                fname = get_fname_from_fid(fid)
        except Exception:
            pass

        if raw_add:
            track_id = raw_add.split("/")[-1].split("?")[0]
            if track_id not in [qi["id"] for qi in queue]:
                print("Adding track to queue", track_id)
                active_device_id = ""
                devices = send_auth_request(username, "/v1/me/player/devices")
                if "devices" in devices:
                    for d in devices["devices"]:
                        if "is_active" in d and d["is_active"]:
                            active_device_id = d["id"]
                send_auth_request(
                    username,
                    f"/v1/me/player/queue?device_id={active_device_id}&uri=spotify:track:{track_id}",
                    method="post",
                )
            if fname:
                attribute_track_addition(username, track_id, f"fname:{fname}")

            return redirect(
                url_for("track_by_user", username=username, track_id=track_id)
                + "?added=true"
            )

        frame_img = generate_frame_for_queue_item(queue[0]) if queue else None
        return render_template(
            "queue.html", username=username, queue=queue, cover_img=frame_img
        )

    except Exception as e:
        print(e)
        return render_template("queue.html")


@app.route("/<string:username>/<string:track_id>", methods=["GET", "POST"])
def track_by_user(username, track_id):
    if request.method == "POST" and not request.args.get("added"):
        return redirect(url_for("now_playing", username=username))

    queue = get_queue(username)
    if not queue:
        return render_template("track.html")

    track = send_auth_request(username, f"/v1/tracks/{track_id}")
    track = simplify_queue_item(track)
    cover_img = generate_frame_for_queue_item(track)

    return render_template(
        "track.html",
        username=username,
        track=track,
        cover_img=cover_img,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
