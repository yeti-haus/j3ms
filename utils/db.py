import os
import psycopg2

conn = psycopg2.connect(os.getenv("POSTGRES_URI"))


def exec_query(query, params=()):
    rows = None
    cur = conn.cursor()
    cur.execute(query, params)
    if "select" in query.lower():
        rows = cur.fetchall()
    conn.commit()
    return rows
