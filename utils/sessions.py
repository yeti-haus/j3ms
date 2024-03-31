from datetime import datetime, timedelta

from .db import exec_query
from .spotify import get_access_token


def store_session(username, auth_resp):
    access_token = auth_resp["access_token"]
    refresh_token = auth_resp["refresh_token"] if "refresh_token" in auth_resp else None
    scope = auth_resp["scope"]
    expires_at = datetime.now() + timedelta(seconds=auth_resp["expires_in"])

    exec_query(
        """
    INSERT INTO sessions
        (username, access_token, refresh_token, scope, expires_at)
        VALUES
        (%s,%s,%s,%s,%s)
        ON CONFLICT (username)
        DO UPDATE SET
            access_token = excluded.access_token,
            refresh_token = (case when excluded.refresh_token is not null then excluded.refresh_token else sessions.refresh_token end),
            scope = excluded.scope,
            expires_at = excluded.expires_at
               """,
        (username, access_token, refresh_token, scope, expires_at),
    )


def get_auth_token(username):
    rows = exec_query(
        f"SELECT access_token FROM sessions WHERE username = '{username}' LIMIT 1"
    )
    if not rows or not rows[0]:
        return None
    return rows[0][0]


def refresh_sessions():
    soon = datetime.now() + timedelta(minutes=60)
    rows_to_refresh = exec_query(
        f"SELECT username, refresh_token FROM sessions WHERE expires_at < '{soon}'"
    )

    for username, refresh_token in rows_to_refresh:
        print("Refreshing", username)
        get_access_token(refresh_token=refresh_token)
        store_session(username, get_access_token(refresh_token=refresh_token))
