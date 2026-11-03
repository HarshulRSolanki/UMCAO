"""Database and persistence layer for UMCAO using SQLite.

Manages users, analysis history, and saved snippets.
Zero external configuration required.
"""

import os
import sqlite3
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment configuration
ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(dotenv_path=ENV_PATH)

db_env = os.getenv("DATABASE_URL", "umcao.db").strip()
if db_env.startswith("sqlite:///"):
    db_file = db_env.replace("sqlite:///", "")
else:
    db_file = db_env

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), db_file)) if not os.path.isabs(db_file) else db_file


def get_db_connection() -> sqlite3.Connection:
    """Connect to SQLite database with foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Initialize database tables on application startup."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)

    # 2. User Sessions / Auth Tokens Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)

    # 3. Analysis History Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            code TEXT NOT NULL,
            language TEXT NOT NULL,
            time_complexity TEXT,
            space_complexity TEXT,
            patterns_count INTEGER DEFAULT 0,
            optimizations_count INTEGER DEFAULT 0,
            execution_time_ms REAL DEFAULT 0,
            memory_kb REAL DEFAULT 0,
            status TEXT DEFAULT 'success',
            response_json TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
        );
    """)

    # 4. Saved Code Snippets Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_snippets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            code TEXT NOT NULL,
            language TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    conn.close()


# -----------------------------------------------------------------------------
# Password & Auth Utilities
# -----------------------------------------------------------------------------
def _hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Hashes a password with PBKDF2-HMAC-SHA256."""
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=100000,
    )
    return key.hex(), salt


def register_user(username: str, email: str, password: str) -> Dict[str, Any]:
    """Registers a new user and returns their user profile and session token."""
    clean_username = username.strip()
    clean_email = email.strip().lower()

    if len(clean_username) < 3:
        raise ValueError("Username must be at least 3 characters long.")
    if "@" not in clean_email or "." not in clean_email:
        raise ValueError("A valid email address is required.")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters long.")

    pw_hash, salt = _hash_password(password)
    now = datetime.now(timezone.utc).isoformat()

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, salt, created_at) VALUES (?, ?, ?, ?, ?)",
            (clean_username, clean_email, pw_hash, salt, now),
        )
        user_id = cursor.lastrowid

        # Create session token
        token = secrets.token_urlsafe(32)
        cursor.execute(
            "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
            (token, user_id, now),
        )
        conn.commit()

        return {
            "token": token,
            "user": {
                "id": user_id,
                "username": clean_username,
                "email": clean_email,
                "created_at": now,
            },
        }
    except sqlite3.IntegrityError as e:
        err_msg = str(e).lower()
        if "username" in err_msg:
            raise ValueError("Username already taken. Please choose another.")
        elif "email" in err_msg:
            raise ValueError("Email already registered. Please sign in.")
        raise ValueError("User registration failed due to unique constraint.")
    finally:
        conn.close()


def authenticate_user(username_or_email: str, password: str) -> Dict[str, Any]:
    """Authenticates user credentials and returns session token and profile."""
    query_str = username_or_email.strip()

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (query_str, query_str.lower()),
        )
        user = cursor.fetchone()

        if not user:
            raise ValueError("Invalid username or password.")

        pw_hash, _ = _hash_password(password, salt=user["salt"])
        if pw_hash != user["password_hash"]:
            raise ValueError("Invalid username or password.")

        # Create session token
        token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
            (token, user["id"], now),
        )
        conn.commit()

        return {
            "token": token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "created_at": user["created_at"],
            },
        }
    finally:
        conn.close()


def get_user_from_token(token: Optional[str]) -> Optional[Dict[str, Any]]:
    """Retrieves user profile associated with session token."""
    if not token:
        return None

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT u.id, u.username, u.email, u.created_at
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ?
            """,
            (token.strip(),),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return dict(row)
    finally:
        conn.close()


# -----------------------------------------------------------------------------
# Analysis History Methods
# -----------------------------------------------------------------------------
def save_analysis_record(
    code: str,
    language: str,
    user_id: Optional[int] = None,
    title: Optional[str] = None,
    time_complexity: Optional[str] = None,
    space_complexity: Optional[str] = None,
    patterns_count: int = 0,
    optimizations_count: int = 0,
    execution_time_ms: float = 0.0,
    memory_kb: float = 0.0,
    status: str = "success",
    response_json: Optional[str] = None,
) -> int:
    """Saves an analysis execution record to SQLite."""
    now = datetime.now(timezone.utc).isoformat()
    if not title:
        first_line = code.strip().splitlines()[0] if code.strip() else "Untitled Snippet"
        title = first_line[:40] if len(first_line) > 40 else first_line

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO analysis_history (
                user_id, title, code, language, time_complexity, space_complexity,
                patterns_count, optimizations_count, execution_time_ms, memory_kb,
                status, response_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                title,
                code,
                language,
                time_complexity,
                space_complexity,
                patterns_count,
                optimizations_count,
                execution_time_ms,
                memory_kb,
                status,
                response_json,
                now,
            ),
        )
        record_id = cursor.lastrowid
        conn.commit()
        return record_id
    finally:
        conn.close()


def get_analysis_history(user_id: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves previous analysis records (per-user or recent global)."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if user_id:
            cursor.execute(
                """
                SELECT id, user_id, title, language, time_complexity, space_complexity,
                       patterns_count, optimizations_count, execution_time_ms, memory_kb,
                       status, created_at, substr(code, 1, 120) as code_preview
                FROM analysis_history
                WHERE user_id = ?
                ORDER BY id DESC LIMIT ?
                """,
                (user_id, limit),
            )
        else:
            cursor.execute(
                """
                SELECT id, user_id, title, language, time_complexity, space_complexity,
                       patterns_count, optimizations_count, execution_time_ms, memory_kb,
                       status, created_at, substr(code, 1, 120) as code_preview
                FROM analysis_history
                ORDER BY id DESC LIMIT ?
                """,
                (limit,),
            )
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_analysis_by_id(record_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves full analysis record by ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analysis_history WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def delete_analysis_record(record_id: int, user_id: Optional[int] = None) -> bool:
    """Deletes an analysis record."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if user_id:
            cursor.execute("DELETE FROM analysis_history WHERE id = ? AND user_id = ?", (record_id, user_id))
        else:
            cursor.execute("DELETE FROM analysis_history WHERE id = ?", (record_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
