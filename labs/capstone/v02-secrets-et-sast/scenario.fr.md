# V2 : deux portes qui bloquent, et le défaut qu'elles arrêtent

## Situation

Le modèle de menace de V1 a nommé ce que le code porte : `GET /notes/search`
colle le terme cherché dans sa requête SQL, et la menace est `open`. Le
pipeline teste, vérifie le modèle, mais ne cherche ni secret ni motif
dangereux. Un jeton collé dans le code, ou une deuxième requête concaténée,
atteindraient `main` sans un mot.

Le répertoire `challenge/work` contient le projet tel que V1 l'a laissé.

Pratiques SSDF visées : PW.7 (analyser le code source pour y trouver les vulnérabilités), PW.5 (écrire le code selon des pratiques de codage sûr).

## Objectif

1. Le pipeline lance une **analyse de secrets** et une **analyse statique**,
   avant les tests, et chacune **bloque** : un constat rend le job rouge.
2. L'injection de `/notes/search` est **corrigée dans le code**, et un test de
   régression la tente : il échouerait si la requête redevenait concaténée.
3. Le modèle de menace dit la vérité sur le code : la menace d'altération de
   `GET /notes/search` passe à `mitigated`, et cite ce test comme preuve.

Le projet doit rester vert. Une copie qui embarque un secret, ou qui ajoute une
route concaténant une valeur dans une requête, doit le rendre rouge, et sur la
bonne porte.

## Repères

- Les deux outils tournent comme étapes `docker://`, image épinglée par digest
  : `zricethezav/gitleaks` et `semgrep/semgrep`.
- Un scanner qui écrit ses constats mais rend 0 ne bloque rien : vérifiez le
  code de sortie de chacun.
- `sqlite3` accepte des paramètres `?` : la valeur voyage à part de la requête.

## Vérifier

```bash
dsoxlab check capstone-v02-secrets-et-sast
```

Cinq contrôles, vingt points chacun. Ils jouent votre pipeline avec act sur le
projet et sur des copies piégées, interrogent l'application, et relisent le
modèle de menace.
