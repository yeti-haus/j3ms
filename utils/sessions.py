from datetime import datetime, timedelta

from .db import exec_query


def store_session(username, auth_resp):
    access_token = auth_resp["access_token"]
    refresh_token = auth_resp["refresh_token"]
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
            refresh_token = excluded.refresh_token,
            scope = excluded.scope,
            expires_at = excluded.expires_at
               """,
        (username, access_token, refresh_token, scope, expires_at),
    )


def get_auth_token(username):
    rows = exec_query(
        f"SELECT access_token FROM sessions WHERE username = '{username}' LIMIT 1"
    )
    return rows[0][0]
