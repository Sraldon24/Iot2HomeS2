import sqlite3, os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "../iot_data.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS environment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                temperature REAL,
                humidity REAL,
                synced INTEGER DEFAULT 0
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS motion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                motion INTEGER,
                image_name TEXT,
                synced INTEGER DEFAULT 0
            )
        """)
        conn.commit()

def save_env(temperature, humidity):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO environment (timestamp, temperature, humidity)
            VALUES (?, ?, ?)
        """, (datetime.now().isoformat(), temperature, humidity))
        conn.commit()

def save_motion(motion, image_name=None):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO motion (timestamp, motion, image_name)
            VALUES (?, ?, ?)
        """, (datetime.now().isoformat(), motion, image_name))
        conn.commit()

def fetch_unsynced(table):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(f"SELECT * FROM {table} WHERE synced=0")
        return c.fetchall()

def mark_synced(table, row_ids):
    if not row_ids: return
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        q = f"UPDATE {table} SET synced=1 WHERE id IN ({','.join('?'*len(row_ids))})"
        c.execute(q, row_ids)
        conn.commit()