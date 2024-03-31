create table sessions (username text unique, access_token text, refresh_token text, scope text, expires_at timestamptz);
