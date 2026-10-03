"""Les tests de notes-api : ce que le service promet à ses clients."""

from __future__ import annotations

import pytest

from notes_api.app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path / "notes.db")
    app.config["TESTING"] = True
    return app.test_client()


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_creer_puis_lister(client):
    reponse = client.post("/notes", json={"owner": "alice", "title": "courses", "body": "pain"})
    assert reponse.status_code == 201
    notes = client.get("/notes", query_string={"owner": "alice"}).get_json()
    assert [n["title"] for n in notes] == ["courses"]


def test_un_utilisateur_ne_voit_que_ses_notes(client):
    client.post("/notes", json={"owner": "alice", "title": "a"})
    client.post("/notes", json={"owner": "bob", "title": "b"})
    notes = client.get("/notes", query_string={"owner": "bob"}).get_json()
    assert [n["owner"] for n in notes] == ["bob"]


def test_chercher_par_titre(client):
    client.post("/notes", json={"owner": "alice", "title": "liste de courses"})
    client.post("/notes", json={"owner": "alice", "title": "vacances"})
    notes = client.get("/notes/search", query_string={"q": "courses"}).get_json()
    assert [n["title"] for n in notes] == ["liste de courses"]


def test_creer_sans_titre_est_refuse(client):
    reponse = client.post("/notes", json={"owner": "alice"})
    assert reponse.status_code == 400
