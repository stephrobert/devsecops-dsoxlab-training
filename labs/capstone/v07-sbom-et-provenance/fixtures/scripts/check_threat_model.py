"""Check that threat-model.yml is complete enough to be reviewed.

    uv run python scripts/check_threat_model.py threat-model.yml

The file lists the threats of notes-api, one entry per threat:

    threats:
      - id: T-01
        stride: T            # one of S, T, R, I, D, E
        component: GET /notes/search
        threat: what can go wrong, and who makes it happen
        mitigation: what reduces it, or will
        status: open         # open, mitigated or accepted
        evidence: tests/test_app.py   # required when status is mitigated

Exit code 0 when the model is valid, 1 when it is not, with one line per
problem. A model that does not cover the six STRIDE categories is not valid:
a category nobody looked at is a blind spot, not an absence of threat.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

STRIDE = {
    "S": "Spoofing",
    "T": "Tampering",
    "R": "Repudiation",
    "I": "Information disclosure",
    "D": "Denial of service",
    "E": "Elevation of privilege",
}
STATUSES = {"open", "mitigated", "accepted"}
REQUIRED = ("id", "stride", "component", "threat", "mitigation", "status")


def problems(path: Path) -> list[str]:
    if not path.is_file():
        return [f"{path}: file not found"]
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [f"{path}: invalid YAML ({exc})"]
    threats = (data or {}).get("threats") if isinstance(data, dict) else None
    if not isinstance(threats, list) or not threats:
        return [f"{path}: no `threats:` list"]

    found: list[str] = []
    seen_ids: set[str] = set()
    covered: set[str] = set()
    root = path.resolve().parent
    for index, threat in enumerate(threats, 1):
        where = f"threat #{index}"
        if not isinstance(threat, dict):
            found.append(f"{where}: an entry must be a mapping")
            continue
        where = f"threat {threat.get('id') or '#' + str(index)}"
        for key in REQUIRED:
            if not str(threat.get(key) or "").strip():
                found.append(f"{where}: `{key}` is missing or empty")
        ident = str(threat.get("id") or "")
        if ident and ident in seen_ids:
            found.append(f"{where}: duplicate id")
        seen_ids.add(ident)
        letter = str(threat.get("stride") or "").strip().upper()
        if letter and letter not in STRIDE:
            found.append(f"{where}: stride `{letter}` is not one of {', '.join(STRIDE)}")
        elif letter:
            covered.add(letter)
        status = str(threat.get("status") or "").strip()
        if status and status not in STATUSES:
            found.append(f"{where}: status `{status}` is not one of {', '.join(sorted(STATUSES))}")
        if status == "mitigated":
            evidence = str(threat.get("evidence") or "").strip()
            if not evidence:
                found.append(f"{where}: a mitigated threat needs `evidence`, the file that proves it")
            elif not (root / evidence).exists():
                found.append(f"{where}: evidence `{evidence}` does not exist in the repository")
    for letter in sorted(set(STRIDE) - covered):
        found.append(f"no threat for {letter} ({STRIDE[letter]}): a category nobody looked at is a blind spot")
    return found


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "threat-model.yml")
    found = problems(path)
    if found:
        for line in found:
            print(f"THREAT-MODEL: {line}")
        print(f"FAILED: {len(found)} problem(s) in {path}")
        return 1
    count = len(yaml.safe_load(path.read_text(encoding="utf-8"))["threats"])
    print(f"threat model valid: {count} threats, 6/6 STRIDE categories")
    return 0


if __name__ == "__main__":
    sys.exit(main())
