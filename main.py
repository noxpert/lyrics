import sqlite3
import os
import webbrowser
import threading
from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
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
                lyrics  TEXT NOT NULL,
                created_at  TEXT DEFAULT (datetime('now')),
                updated_at  TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()

# ── Pydantic models ──────────────────────────────────────────────────────────

class SongIn(BaseModel):
    title: str
    lyrics: str

class SongOut(BaseModel):
    id: int
    title: str
    lyrics: str

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
    row = conn.execute("SELECT id, title, lyrics FROM songs WHERE id = ?", (song_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Song not found")
    return dict(row)

@app.post("/api/songs", status_code=201)
def create_song(song: SongIn):
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO songs (title, lyrics) VALUES (?, ?)",
            (song.title.strip(), song.lyrics)
        )
        conn.commit()
        return {"id": cur.lastrowid, "title": song.title.strip()}
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
            "UPDATE songs SET title = ?, lyrics = ?, updated_at = datetime('now') WHERE id = ?",
            (song.title.strip(), song.lyrics, song_id)
        )
        conn.commit()
        return {"id": song_id, "title": song.title.strip()}
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
