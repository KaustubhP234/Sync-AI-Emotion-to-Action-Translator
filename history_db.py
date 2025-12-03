# backend/history_db.py
import sqlite3
from datetime import datetime

DB_PATH = "models/history.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # history table
    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            input_type TEXT,
            filename TEXT,
            emotion TEXT,
            confidence REAL,
            action TEXT
        )
    """)
    # alerts table
    c.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            from_emotion TEXT,
            to_emotion TEXT,
            magnitude INTEGER,
            confidence_from REAL,
            confidence_to REAL,
            metadata TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_prediction(input_type, filename, emotion, confidence, action):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO history (timestamp, input_type, filename, emotion, confidence, action)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (datetime.now().isoformat(), input_type, filename, emotion, confidence, action))
    conn.commit()
    conn.close()

def get_history(limit=50):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [
        {
            "timestamp": r[1],
            "input_type": r[2],
            "filename": r[3],
            "emotion": r[4],
            "confidence": r[5],
            "action": r[6],
        }
        for r in rows
    ]

def log_alert(from_emotion, to_emotion, magnitude, confidence_from=None, confidence_to=None, metadata=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO alerts (timestamp, from_emotion, to_emotion, magnitude, confidence_from, confidence_to, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (datetime.now().isoformat(), from_emotion, to_emotion, magnitude, confidence_from or 0.0, confidence_to or 0.0, metadata))
    conn.commit()
    conn.close()

def get_alerts(limit=50):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [
        {
            "timestamp": r[1],
            "from": r[2],
            "to": r[3],
            "magnitude": r[4],
            "confidence_from": r[5],
            "confidence_to": r[6],
            "metadata": r[7]
        }
        for r in rows
    ]
