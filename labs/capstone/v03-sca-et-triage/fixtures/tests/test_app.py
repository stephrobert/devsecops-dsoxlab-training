"""Les tests de notes-api : ce que le service promet à ses clients."""

from __future__ import annotations

import hashlib
import json

import pytest
from ecdsa import NIST256p, SigningKey

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


def test_la_recherche_resiste_a_l_injection_sql(client):
    """Le terme cherché est une valeur, jamais un morceau de requête."""
    client.post("/notes", json={"owner": "alice", "title": "liste de courses"})
    client.post("/notes", json={"owner": "bob", "title": "secret de bob"})
    reponse = client.get("/notes/search", query_string={"q": "' OR '1'='1"})
    assert reponse.status_code == 200
    assert reponse.get_json() == []


@pytest.fixture
def emetteur():
    """La clé de l'autre service : jetable, créée pour le test et jamais versionnée."""
    return SigningKey.generate(curve=NIST256p)


@pytest.fixture
def client_import(tmp_path, emetteur):
    cle_publique = emetteur.get_verifying_key().to_pem().decode()
    app = create_app(tmp_path / "notes.db", import_public_key=cle_publique)
    app.config["TESTING"] = True
    return app.test_client()


def _lot_signe(cle, notes):
    corps = json.dumps(notes).encode()
    return corps, cle.sign(corps, hashfunc=hashlib.sha256).hex()


def test_import_signe_accepte(client_import, emetteur):
    corps, signature = _lot_signe(emetteur, [{"owner": "alice", "title": "importée"}])
    reponse = client_import.post("/notes/import", data=corps, headers={"X-Signature": signature})
    assert reponse.status_code == 201
    notes = client_import.get("/notes", query_string={"owner": "alice"}).get_json()
    assert [n["title"] for n in notes] == ["importée"]


def test_import_signe_par_une_autre_cle_refuse(client_import):
    intrus = SigningKey.generate(curve=NIST256p)
    corps, signature = _lot_signe(intrus, [{"owner": "alice", "title": "forgée"}])
    reponse = client_import.post("/notes/import", data=corps, headers={"X-Signature": signature})
    assert reponse.status_code == 401


def test_import_sans_cle_configuree_desactive(client):
    assert client.post("/notes/import", data=b"[]").status_code == 503
