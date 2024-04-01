import requests


def get_fname_from_fid(fid):
    r = requests.get(f"https://hub.pinata.cloud/v1/userDataByFid?fid={fid}")
    messages = r.json()["messages"]

    for m in messages:
        try:
            if m["data"]["userDataBody"]["type"] == "USER_DATA_TYPE_USERNAME":
                return m["data"]["userDataBody"]["value"]
        except Exception:
            pass

    return None
