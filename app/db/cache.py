import sqlite3
import os
from app.config.settings import Settings

def get_connection():
    os.makedirs(os.path.dirname(Settings.DB_PATH), exist_ok=True)
    conn = sqlite3.connect(Settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS medicine_explanations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_name TEXT UNIQUE NOT NULL,
            medicine_name_lower TEXT NOT NULL,
            explanation TEXT NOT NULL,
            model_used TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            access_count INTEGER DEFAULT 1
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS query_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_type TEXT,
            ocr_confidence REAL,
            medicines_found INTEGER,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Database initialised")

def get_cached_explanation(medicine_name: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT explanation FROM medicine_explanations WHERE medicine_name_lower = ?",
        (medicine_name.lower(),)
    ).fetchone()
    if row:
        conn.execute(
            "UPDATE medicine_explanations SET access_count = access_count + 1 WHERE medicine_name_lower = ?",
            (medicine_name.lower(),)
        )
        conn.commit()
    conn.close()
    return row["explanation"] if row else None

def cache_explanation(medicine_name: str, explanation: str, model: str = ""):
    conn = get_connection()
    conn.execute("""
        INSERT OR REPLACE INTO medicine_explanations
        (medicine_name, medicine_name_lower, explanation, model_used)
        VALUES (?, ?, ?, ?)
    """, (medicine_name, medicine_name.lower(), explanation, model))
    conn.commit()
    conn.close()

def log_query(input_type: str, ocr_confidence: float, medicines_found: int):
    conn = get_connection()
    conn.execute("""
        INSERT INTO query_log (input_type, ocr_confidence, medicines_found)
        VALUES (?, ?, ?)
    """, (input_type, ocr_confidence, medicines_found))
    conn.commit()
    conn.close()
