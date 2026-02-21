"""
BudgetX - SQLite Database Module
Handles database initialization, user management, chat history, and file records.
"""

import sqlite3
import os
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "budgetx.db")


def get_connection():
    """Get a new SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize the database with all required tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # Users table - stores credentials
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Chat history table - stores each user's conversation with AI
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Uploaded files table - tracks CSV files uploaded by each user
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            original_filename TEXT NOT NULL,
            stored_filename TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            upload_date TEXT NOT NULL DEFAULT (datetime('now')),
            analytics_json TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# User operations
# ---------------------------------------------------------------------------

def create_user(username: str, password_hash: str) -> int:
    """Insert a new user. Returns the new user ID."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_user_by_username(username: str):
    """Return a user row dict or None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Chat history operations
# ---------------------------------------------------------------------------

def save_chat_message(user_id: int, role: str, content: str) -> int:
    """Save a single chat message. Returns the message ID."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_chat_history(user_id: int, limit: int = 50) -> list:
    """Return recent chat messages for a user, oldest first."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT id, role, content, timestamp
               FROM chat_history
               WHERE user_id = ?
               ORDER BY id DESC
               LIMIT ?""",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]
    finally:
        conn.close()


def clear_chat_history(user_id: int):
    """Delete all chat messages for a user."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Uploaded file operations
# ---------------------------------------------------------------------------

def save_file_record(
    user_id: int,
    original_filename: str,
    stored_filename: str,
    file_size: int,
    analytics_json: str = None,
) -> int:
    """Record a file upload. Returns the file record ID."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO uploaded_files
               (user_id, original_filename, stored_filename, file_size, analytics_json)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, original_filename, stored_filename, file_size, analytics_json),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_user_files(user_id: int) -> list:
    """Return all files uploaded by a user, newest first."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT id, original_filename, stored_filename, file_size,
                      upload_date, analytics_json
               FROM uploaded_files
               WHERE user_id = ?
               ORDER BY id DESC""",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_file_by_id(file_id: int, user_id: int):
    """Return a single file record or None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM uploaded_files WHERE id = ? AND user_id = ?",
            (file_id, user_id),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_file_analytics(file_id: int, analytics_json: str):
    """Update the stored analytics JSON for a file."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE uploaded_files SET analytics_json = ? WHERE id = ?",
            (analytics_json, file_id),
        )
        conn.commit()
    finally:
        conn.close()


# Initialize the database on module import
init_db()
