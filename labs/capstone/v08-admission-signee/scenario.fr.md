# V8 : le cluster refuse ce que la plateforme n'a pas signé

## Situation

Tout ce que V1 à V7 ont construit s'arrête aux portes du cluster. Les images
de notes-api partent dans le registre interne `registry.notes.internal:5000`,
où la plateforme les signe avec sa clé KMS. Mais le cluster ne vérifie rien :
une image poussée à la main, une image de Docker Hub, ou un tag déplacé après
l'analyse démarrent dans l'espace de noms `notes-api` comme les autres. Le
modèle de menace la nomme : T-15, `open`.

La clé publique de la plateforme est `deploy/signing/cosign.pub`. Le cluster
fait tourner **Kyverno 1.19**.

Le répertoire `challenge/work` contient le projet tel que V7 l'a laissé, avec
cette clé.

Pratique SSDF visée : PS.2 (permettre de vérifier l'intégrité des versions publiées).

## Objectif

Écrire, dans `deploy/policies/`, les politiques d'admission de l'espace de
noms `notes-api` :

1. une image du registre interne **signée par la clé de la plateforme** est
   **admise** ;
2. une image **non signée**, ou **signée par une autre clé**, est **refusée**,
   et un Deployment qui la nomme est refusé dès sa création ;
3. une image venue d'**un autre registre** est **refusée** dans `notes-api`,
   et seulement là : le reste du cluster n'est pas concerné ;
4. la menace T-15 passe à `mitigated`, avec une politique comme preuve.

## Repères

- Kyverno 1.19 déprécie `ClusterPolicy` : écrivez une `ImageValidatingPolicy`
  pour la signature, et une `ValidatingPolicy` pour le registre, toutes deux
  en `policies.kyverno.io/v1`.
- La vérification ne se déclenche que si une validation appelle
  `verifyImageSignatures`. Le nom d'un attestor ne porte pas de tiret : il est
  lu dans une expression CEL.
- La clé publique se recopie dans la politique (`key.data`). Le registre
  interne n'inscrit pas les signatures dans un journal de transparence
  public : `ctlog.insecureIgnoreTlog: true`.
- `namespaceSelector` sur `kubernetes.io/metadata.name` limite une politique
  à un espace de noms.

## Vérifier

```bash
dsoxlab check capstone-v08-admission-signee
```

Cinq contrôles, vingt points chacun. Ils montent un cluster kind avec le
registre interne et Kyverno, y appliquent vos politiques, puis demandent
l'admission d'images signées, non signées et étrangères. Comptez trois à
quatre minutes.
