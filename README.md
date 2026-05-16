# Lyrics App

A local lyrics viewer and editor. Runs entirely offline on your Mac.

## Setup (one time only)

1. **Copy the `lyricsapp` folder** anywhere you like — your Desktop, Documents, wherever.

2. **Make the launch script executable.** Open Terminal, `cd` to the folder, and run:
   ```
   chmod +x "Launch Lyrics.command"
   ```

3. That's it.

## Launching

Double-click **`Launch Lyrics.command`** in Finder.

- The first launch installs dependencies into a local `.venv` folder (takes ~15 seconds).
- Subsequent launches open in a few seconds.
- Your browser opens automatically to `http://localhost:8765`.

> **macOS Gatekeeper note:** The first time you double-click the `.command` file, macOS
> may warn you it's from an unidentified developer. Right-click → Open → Open to allow it.

## Stopping the server

Close the Terminal window that opened, or press **Ctrl-C** in it.

## Data

All songs are stored in `lyrics.db` (SQLite) in the app folder. Back it up like any file.

## Folder structure

```
lyricsapp/
├── Launch Lyrics.command   ← double-click to start
├── main.py                 ← FastAPI server
├── requirements.txt        ← Python dependencies
├── lyrics.db               ← created on first run
├── .venv/                  ← created on first run
└── static/
    └── index.html          ← the web UI
```

## Usage

- **Browse tab** — searchable, scrollable song list on the left; lyrics displayed large on the right.
  - Click any song to view it.
  - Click **"Edit this song"** to jump to the editor.
- **Edit tab** — pick an existing song from the left panel, or click **+ New**.
  - Enter/paste lyrics (line breaks are preserved exactly as typed).
  - Click **Save** to persist, or **Delete song** to remove.
