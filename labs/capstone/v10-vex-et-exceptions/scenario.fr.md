# V10 : chaque constat accepté est écrit, daté et publié

## Situation

Jusqu'ici, le pipeline de notes-api ne bloquait qu'au seuil HIGH. L'équipe
le relève à **MEDIUM**, pour l'image comme pour la configuration. Trois
constats de configuration remontent aussitôt :

- AWS-0090 sur `infra/deploy.tf` : le bucket des versions n'a pas de
  versioning ;
- AWS-0090 sur `infra/main.tf` : le bucket des exports non plus ;
- KSV-0125 sur `deploy/k8s/deployment.yaml` : l'image vient d'un registre que
  Trivy ne connaît pas.

Côté image, Trivy signale **pip 25.0.1**, venu de l'image de base, avec
plusieurs vulnérabilités MEDIUM. notes-api n'exécute jamais pip. Les images
déjà livrées le contiennent pourtant, et les scanners de ceux qui les
exploitent les signalent. Le modèle de menace le nomme : T-17, `open`.

Le répertoire `challenge/work` contient le projet tel que V9 l'a laissé.

Pratique SSDF visée : RV.2 (évaluer, prioriser et corriger les vulnérabilités).

## Objectif

1. Les analyses `config` et `image` de Trivy **bloquent au seuil MEDIUM**.
2. Ce qui se corrige est **corrigé** : le bucket des versions active le
   versioning, et l'image finale **ne contient plus pip**.
3. Ce qui s'accepte est une **exception datée** dans `.trivyignore.yaml` :
   limitée à son fichier, avec sa raison, et une échéance dans les six mois.
4. `security/notes-api.openvex.json` est un document **VEX** qui déclare
   chaque vulnérabilité de pip `not_affected` pour les versions déjà livrées,
   avec sa justification, et rien d'autre.
5. La menace T-17 passe à `mitigated`, avec sa preuve.

Une copie dont les exceptions ont expiré doit rendre le pipeline rouge.

## Repères

- `--ignorefile .trivyignore.yaml` lit les exceptions ; une entrée porte
  `id`, `paths`, `statement` et `expired_at`. `--skip-check-update` fige les
  contrôles à ceux de la version de Trivy épinglée.
- Le registre interne est inconnu de Trivy, mais un contrôle le garantit
  déjà : la politique d'admission de V8. Une exception peut s'appuyer sur un
  **contrôle compensatoire**, à condition de le nommer.
- OpenVEX : `"products": [{"@id": "pkg:pypi/pip@25.0.1"}]`, `"status":
  "not_affected"` et une `justification` normalisée. `--vex <fichier>` le fait
  lire à Trivy.
- Retirer un outil inutile vaut mieux que d'expliquer pourquoi ses failles ne
  comptent pas : le VEX sert aux versions qu'on ne peut plus reconstruire.

## Vérifier

```bash
dsoxlab check capstone-v10-vex-et-exceptions
```

Cinq contrôles, vingt points chacun. Ils jouent votre pipeline avec act,
construisent votre image et celle de la version précédente, analysent la
seconde avec votre VEX, et rejouent le pipeline sur une copie aux exceptions
expirées.
