import os
import psycopg2

conn = None


def exec_query(query, params=()):
    global conn
    if not conn:
        conn = psycopg2.connect(os.getenv("POSTGRES_URI"))
        setup_script = open("assets/setup.sql", "r")
        lines = setup_script.readlines()
        cur = conn.cursor()
        for line in lines:
            print(line)
            cur.execute(line)
        conn.commit()

    rows = None
    cur = conn.cursor()
    cur.execute(query, params)
    if "select" in query.lower():
        rows = cur.fetchall()
    conn.commit()
    return rows
