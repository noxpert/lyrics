import json
import sqlite3
import os
import webbrowser
import threading
from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, field_validator
from typing import Optional

# ── Database setup ──────────────────────────────────────────────────────────

DB_PATH = Path(__file__).parent / "lyrics.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                title   TEXT NOT NULL UNIQUE COLLATE NOCASE,
                lyrics_json  TEXT NOT NULL,
                created_at  TEXT DEFAULT (datetime('now')),
                updated_at  TEXT DEFAULT (datetime('now'))
            )
        """)
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(songs)")}
        if "lyrics" in cols and "lyrics_json" not in cols:
            conn.execute("ALTER TABLE songs RENAME COLUMN lyrics TO lyrics_json")
            cols = {r["name"] for r in conn.execute("PRAGMA table_info(songs)")}
        if "lyrics_json" in cols:
            for row in conn.execute("SELECT id, lyrics_json FROM songs"):
                raw = row["lyrics_json"]
                if not is_json_string_array(raw):
                    conn.execute(
                        "UPDATE songs SET lyrics_json = ? WHERE id = ?",
                        (json.dumps([raw]), row["id"]),
                    )
        conn.commit()

def is_json_string_array(value: str) -> bool:
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return False
    return isinstance(parsed, list) and all(isinstance(item, str) for item in parsed)

# ── Pydantic models ──────────────────────────────────────────────────────────

class SongIn(BaseModel):
    title: str
    lyrics: list[str]

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        title = v.strip()
        if not title:
            raise ValueError("title cannot be empty")
        return title

    @field_validator("lyrics")
    @classmethod
    def validate_lyrics(cls, v):
        if not (1 <= len(v) <= 3):
            raise ValueError("lyrics must have 1, 2, or 3 columns")
        if not any(s.strip() for s in v):
            raise ValueError("lyrics cannot be entirely empty")
        return v

class SongOut(BaseModel):
    id: int
    title: str
    lyrics: list[str]

# ── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(title="Lyrics App")

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.on_event("startup")
def startup():
    init_db()

# ── API routes ───────────────────────────────────────────────────────────────

@app.get("/api/songs")
def list_songs(q: Optional[str] = None):
    conn = get_db()
    if q:
        rows = conn.execute(
            "SELECT id, title FROM songs WHERE title LIKE ? ORDER BY title COLLATE NOCASE",
            (f"%{q}%",)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, title FROM songs ORDER BY title COLLATE NOCASE"
        ).fetchall()
    return [dict(r) for r in rows]

@app.get("/api/songs/{song_id}")
def get_song(song_id: int):
    conn = get_db()
    row = conn.execute("SELECT id, title, lyrics_json FROM songs WHERE id = ?", (song_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Song not found")
    return {
        "id": row["id"],
        "title": row["title"],
        "lyrics": json.loads(row["lyrics_json"]),
    }

@app.post("/api/songs", status_code=201)
def create_song(song: SongIn):
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO songs (title, lyrics_json) VALUES (?, ?)",
            (song.title, json.dumps(song.lyrics))
        )
        conn.commit()
        return {"id": cur.lastrowid, "title": song.title}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="A song with that title already exists")

@app.put("/api/songs/{song_id}")
def update_song(song_id: int, song: SongIn):
    conn = get_db()
    row = conn.execute("SELECT id FROM songs WHERE id = ?", (song_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Song not found")
    try:
        conn.execute(
            "UPDATE songs SET title = ?, lyrics_json = ?, updated_at = datetime('now') WHERE id = ?",
            (song.title, json.dumps(song.lyrics), song_id)
        )
        conn.commit()
        return {"id": song_id, "title": song.title}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="A song with that title already exists")

@app.delete("/api/songs/{song_id}", status_code=204)
def delete_song(song_id: int):
    conn = get_db()
    conn.execute("DELETE FROM songs WHERE id = ?", (song_id,))
    conn.commit()

# ── Serve the SPA for all non-API routes ─────────────────────────────────────

@app.get("/{full_path:path}", response_class=HTMLResponse)
def serve_spa(full_path: str):
    return FileResponse(static_dir / "index.html")

# ── Dev entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    def open_browser():
        import time; time.sleep(1)
        webbrowser.open("http://localhost:8765")
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("main:app", host="127.0.0.1", port=8765, reload=False)
