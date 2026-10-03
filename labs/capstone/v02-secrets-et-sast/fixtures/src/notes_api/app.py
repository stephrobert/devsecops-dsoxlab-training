"""notes-api : un petit service de notes, point de départ du fil rouge.

Chaque utilisateur range des notes ; l'API les liste, les cherche et en crée.
Le service tient dans un fichier SQLite, créé au premier appel.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import Flask, g, jsonify, request

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT ''
);
"""


def create_app(database: str | Path = "notes.db") -> Flask:
    app = Flask(__name__)
    app.config["DATABASE"] = str(database)

    def db() -> sqlite3.Connection:
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
            g.db.executescript(SCHEMA)
        return g.db

    @app.teardown_appcontext
    def fermer(_exc: BaseException | None) -> None:
        connexion = g.pop("db", None)
        if connexion is not None:
            connexion.close()

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/notes")
    def lister():
        owner = request.args.get("owner", "")
        lignes = db().execute(
            "SELECT id, owner, title, body FROM notes WHERE owner = ? ORDER BY id", (owner,)
        ).fetchall()
        return jsonify([dict(ligne) for ligne in lignes])

    @app.get("/notes/search")
    def chercher():
        terme = request.args.get("q", "")
        lignes = db().execute(
            "SELECT id, owner, title, body FROM notes WHERE title LIKE '%" + terme + "%' ORDER BY id"
        ).fetchall()
        return jsonify([dict(ligne) for ligne in lignes])

    @app.post("/notes")
    def creer():
        donnees = request.get_json(silent=True) or {}
        owner, title = donnees.get("owner"), donnees.get("title")
        if not owner or not title:
            return jsonify(error="owner et title sont obligatoires"), 400
        curseur = db().execute(
            "INSERT INTO notes (owner, title, body) VALUES (?, ?, ?)",
            (owner, title, donnees.get("body", "")),
        )
        db().commit()
        return jsonify(id=curseur.lastrowid, owner=owner, title=title), 201

    return app
