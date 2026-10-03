# V1 : écrire ce qui peut mal tourner

## Situation

notes-api a son pipeline : chaque push lance les tests. Mais les tests
vérifient ce que le service **promet**, pas ce qu'un attaquant peut en
**faire**. Avant d'ajouter le moindre scanner, l'équipe veut savoir ce qu'elle
protège et contre quoi, et le garder à jour avec le code.

Le répertoire `challenge/work` contient le projet tel que V0 l'a laissé, plus
un outil que l'équipe vient d'écrire : `scripts/check_threat_model.py`. Lancé
sur un `threat-model.yml`, il refuse un modèle incomplet, une catégorie STRIDE
oubliée, une menace déclarée traitée sans fichier qui le prouve. Son en-tête
décrit le format attendu.

Pratique SSDF visée : PW.1 (concevoir le logiciel pour répondre aux exigences et réduire les risques).

## Objectif

1. Un `threat-model.yml` à la racine du projet, que le vérificateur accepte :
   les six catégories STRIDE, chaque menace avec son composant, sa mitigation
   et son statut.
2. Chaque **route** que `src/notes_api/app.py` déclare y est analysée, nommée
   comme la route : `GET /notes/search`.
3. Le défaut que le code porte aujourd'hui y est nommé **tel qu'il est** : une
   menace qui reste `open` tant qu'aucune version ne l'a corrigée.
4. Le pipeline lance le vérificateur à chaque push : un modèle cassé ne doit
   pas atteindre `main`.

## Repères

- Lisez `app.py` fonction par fonction, et demandez-vous pour chaque route :
  qui l'appelle, que croit-elle de ce qu'on lui envoie ?
- STRIDE : usurpation (S), altération (T), répudiation (R), divulgation (I),
  déni de service (D), élévation de privilège (E).
- Une menace `mitigated` doit nommer dans `evidence` le fichier qui le prouve.

## Vérifier

```bash
dsoxlab check capstone-v01-modele-de-menace
```

Cinq contrôles, vingt points chacun. Trois lisent votre modèle et le
confrontent au code ; deux jouent votre pipeline avec act, sur le projet et sur
une copie dont le modèle est cassé.
