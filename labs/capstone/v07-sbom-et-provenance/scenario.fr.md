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
