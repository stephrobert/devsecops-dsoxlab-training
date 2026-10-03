"""notes-api : un petit service de notes, point de départ du fil rouge.

Chaque utilisateur range des notes ; l'API les liste, les cherche et en crée.
Le service tient dans un fichier SQLite, créé au premier appel.

Un lot de notes peut aussi être importé d'un autre service, signé en ECDSA
P-256 : notes-api ne fait que VÉRIFIER la signature, avec la clé publique de
l'émetteur. Elle ne signe jamais rien et ne détient aucune clé privée.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from flask import Flask, g, jsonify, request

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT ''
);
"""


def create_app(database: str | Path = "notes.db", import_public_key: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config["DATABASE"] = str(database)
    app.config["IMPORT_PUBLIC_KEY"] = import_public_key

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
            "SELECT id, owner, title, body FROM notes WHERE title LIKE ? ORDER BY id", (f"%{terme}%",)
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

    @app.post("/notes/import")
    def importer():
        cle = app.config["IMPORT_PUBLIC_KEY"]
        if not cle:
            return jsonify(error="import désactivé : aucune clé publique configurée"), 503
        corps = request.get_data()
        try:
            signature = bytes.fromhex(request.headers.get("X-Signature", ""))
            load_pem_public_key(cle.encode()).verify(signature, corps, ec.ECDSA(hashes.SHA256()))
        except (InvalidSignature, ValueError):
            return jsonify(error="signature invalide"), 401
        notes = json.loads(corps)
        for note in notes:
            db().execute(
                "INSERT INTO notes (owner, title, body) VALUES (?, ?, ?)",
                (note["owner"], note["title"], note.get("body", "")),
            )
        db().commit()
        return jsonify(imported=len(notes)), 201

    return app
