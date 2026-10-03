#!/usr/bin/env bash
# Vérifie qu'une archive de notes-api vient du pipeline de main, avant de la
# déployer.
#
#     scripts/verify_release.sh notes-api-<sha>.tgz
#
# L'attestation doit avoir été signée par le workflow ci.yml de acme/notes-api,
# pour la référence refs/heads/main, sur un runner hébergé par GitHub. Une
# archive remplacée dans le bucket, ou construite depuis une branche, échoue.
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage : $0 <archive>" >&2
  exit 2
fi

gh attestation verify "$1" \
  --repo acme/notes-api \
  --signer-workflow acme/notes-api/.github/workflows/ci.yml \
  --source-ref refs/heads/main \
  --deny-self-hosted-runners
