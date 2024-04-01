create table if not exists sessions (username text unique, access_token text, refresh_token text, scope text, expires_at timestamptz);
create table if not exists queue_adds (timestamp timestamptz, username text, track_id text, dj text, primary key (username, track_id, timestamp));
