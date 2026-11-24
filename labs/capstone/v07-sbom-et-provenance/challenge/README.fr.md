# V7 : savoir ce qu'on livre, prouver d'où ça vient

## Situation

Le pipeline de notes-api analyse le code, les dépendances, les workflows,
l'image et l'infrastructure, puis le job `deploy` publie une archive dans le
bucket `notes-api-releases`. Celui qui déploie ensuite cette archive ne sait
rien d'elle : ni ce qu'elle contient, ni quel pipeline l'a construite. Une
archive remplacée dans le bucket, ou construite depuis une branche, se
déploierait comme les autres. Le modèle de menace la nomme : T-14, `open`.

L'équipe a écrit `scripts/check_sbom.py` : il confronte un SBOM CycloneDX à
`uv.lock` et signale tout paquet de l'environnement de l'application qui n'est
pas verrouillé, ou pas à la bonne version.

Le répertoire `challenge/work` contient le projet tel que V6 l'a laissé, avec
cet outil.

Pratiques SSDF visées : PS.2 (permettre de vérifier l'intégrité des versions publiées), PS.3 (archiver et protéger chaque version publiée).

## Objectif

1. Le pipeline produit le **SBOM de l'image construite**, au format
   CycloneDX, le **confronte à `uv.lock`** avec l'outil de l'équipe, et
   conserve le SBOM comme artefact du run.
2. Le job de déploiement **atteste la provenance** de l'archive qu'il publie
   (attestation SLSA signée par Sigstore), et publie le SBOM à côté d'elle.
3. `scripts/verify_release.sh <archive>` **vérifie l'attestation** avant
   tout déploiement : dépôt `acme/notes-api`, workflow `ci.yml`, référence
   `refs/heads/main`, runner hébergé par GitHub. Il échoue quand la
   vérification échoue.
4. La menace T-14 passe à `mitigated`, avec ce script comme preuve.

Le projet doit rester vert sur une pull request. Une copie dont l'image
installe un paquet hors du verrou doit le rendre rouge.

## Repères

- Trivy, déjà épinglé en V6, produit un SBOM :
  `image --input notes-api.tar --format cyclonedx --output sbom.cdx.json`.
- act ne fournit pas de jeton OIDC : il ne peut pas signer d'attestation. Les
  contrôles relisent donc le job de déploiement, et exécutent votre script de
  vérification avec un faux `gh` qui enregistre ses arguments.
- Sous act 0.2.89, `upload-artifact` au-delà de v5 et `download-artifact`
  au-delà de v6 échouent contre le serveur d'artefacts local : épinglez
  v5.0.0 et v6.0.0.
- `gh attestation verify --help` liste les options qui restreignent le
  signataire accepté.

## Vérifier

```bash
dsoxlab check capstone-v07-sbom-et-provenance
```

Cinq contrôles, vingt points chacun. Ils jouent votre pipeline avec act sur
une pull request et sur une copie piégée, relisent le job de déploiement, et
exécutent votre script de vérification.

## SBOM et provenance

5 tâches, 100 points, 55 minutes.

Le projet est dans `challenge/work`. Vous faites évoluer
`.github/workflows/ci.yml` et `threat-model.yml`, et vous créez
`scripts/verify_release.sh`.

### Tâche 1 : le SBOM de l'image est confronté au verrou (20 pts)

`act pull_request` est vert, et le job montre la ligne
« SBOM matches uv.lock » de l'outil de l'équipe.

### Tâche 2 : un paquet hors du verrou arrête le pipeline (20 pts)

Dans une copie dont l'image installe `six` hors de `uv.lock`, le job échoue
sur la confrontation du SBOM.

### Tâche 3 : le déploiement atteste la provenance de l'archive (20 pts)

Le job de déploiement, réservé à main, déclare `id-token: write` et
`attestations: write`, et atteste l'archive `.tgz` avec une action épinglée
par SHA.

### Tâche 4 : la vérification exige le dépôt, le workflow et main (20 pts)

`scripts/verify_release.sh <archive>` appelle `gh attestation verify` avec
le dépôt, le workflow signataire, la référence et le refus des runners
auto-hébergés, et échoue quand la vérification échoue.

### Tâche 5 : le SBOM est publié, le modèle à jour (20 pts)

Le job de déploiement publie `sbom.cdx.json` à côté de l'archive, et T-14 est
`mitigated` avec sa preuve.
