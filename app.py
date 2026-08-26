from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sqlite3
import os

app = FastAPI(title="Notes Application")

DB_FILE = os.getenv("DB_FILE", "notes.db")


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


class Note(BaseModel):
    title: str
    content: str


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/notes")
def get_notes():
    conn = get_db()

    notes = conn.execute(
        "SELECT * FROM notes ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return [dict(note) for note in notes]


@app.post("/api/notes")
def create_note(note: Note):
    conn = get_db()

    cursor = conn.execute(
        "INSERT INTO notes (title, content) VALUES (?, ?)",
        (note.title, note.content)
    )

    conn.commit()

    note_id = cursor.lastrowid

    conn.close()

    return {
        "id": note_id,
        "title": note.title,
        "content": note.content
    }


@app.delete("/api/notes/{note_id}")
def delete_note(note_id: int):
    conn = get_db()

    cursor = conn.execute(
        "DELETE FROM notes WHERE id = ?",
        (note_id,)
    )

    conn.commit()

    deleted = cursor.rowcount

    conn.close()

    if deleted == 0:
        raise HTTPException(
            status_code=404,
            detail="Note not found"
        )

    return {
        "message": "Note deleted successfully"
    }


app.mount("/", StaticFiles(directory="static", html=True), name="static")
