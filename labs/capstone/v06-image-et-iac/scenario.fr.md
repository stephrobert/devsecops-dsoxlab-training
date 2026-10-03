# V6 : ce que l'on livre, au-delà du code

## Situation

Le pipeline de notes-api relit le code, les dépendances et les workflows. Il
ne regarde ni l'**image** qui part en production, ni l'**infrastructure** qui
l'accueille, et le modèle de menace y garde deux menaces ouvertes depuis V1 :

- T-09 : le `Dockerfile` part de `python:3.12` sans digest, installe des
  versions recopiées à la main dans une ligne `pip install`, et lance le
  service en root ;
- T-10 : `infra/main.tf` ouvre SSH et l'API à `0.0.0.0/0`, et les deux
  buckets n'ont ni blocage d'accès public ni chiffrement par une clé gérée.

Le répertoire `challenge/work` contient le projet tel que V5 l'a laissé.

Pratique SSDF visée : PW.6 (configurer la compilation et le build pour durcir l'exécutable).

## Objectif

1. Le pipeline **analyse la configuration** (Dockerfile et Terraform) et
   **l'image construite**, et chaque analyse **bloque** au seuil HIGH et
   CRITICAL. Pour l'image, seul ce qui a un correctif publié bloque.
2. Le **Dockerfile** part d'images épinglées par digest, installe les
   dépendances depuis `uv.lock` sans le groupe de développement, applique les
   correctifs Debian publiés, et tourne sous un **utilisateur sans
   privilège**.
3. L'**infrastructure** n'expose plus rien à Internet : plus de SSH, l'API
   joignable depuis le VPC seulement ; chaque bucket bloque l'accès public et
   chiffre avec une clé KMS dont la rotation est active.
4. T-09 et T-10 passent à `mitigated`, chacune avec sa preuve.

Le projet doit rester vert sur une pull request. Une copie dont le Dockerfile
perd son `USER`, ou qui ouvre SSH au monde, doit le rendre rouge.

## Repères

- Trivy tourne comme étape `docker://`, image épinglée par digest : `config`
  pour la configuration, `image --input <archive>` pour une image sauvée par
  `docker save`. Évitez les versions 0.69.4 à 0.69.6, compromises en mars
  2026.
- Une image de base figée vieillit : la reconstruire avec
  `apt-get upgrade` applique les correctifs publiés depuis.
- Les constats MEDIUM et LOW qui restent (journalisation, versioning des
  buckets) sont sous le seuil : c'est une décision, à écrire, pas un oubli.

## Vérifier

```bash
dsoxlab check capstone-v06-image-et-iac
```

Cinq contrôles, vingt points chacun. Ils jouent votre pipeline avec act sur
une pull request et sur des copies piégées, construisent votre image pour
l'interroger, et relisent l'infrastructure et le modèle de menace.
