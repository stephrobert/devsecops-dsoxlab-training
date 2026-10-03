# V11 : savoir avant les utilisateurs, et mesurer la livraison

## Situation

De V0 à V10, notes-api est devenue difficile à attaquer. Rien ne dit pourtant
à l'équipe que le service est tombé : ce sont les utilisateurs qui le
remarquent, et la personne d'astreinte cherche alors comment le rétablir. Le
modèle de menace la nomme : T-18, `open`.

L'équipe s'est fixé un objectif de service (SLO) : **99,5 % des requêtes**
servies sans erreur 5xx, sur **28 jours**. Le budget d'erreurs est donc de
0,5 %. La plateforme expose le compteur `http_requests_total`, avec les
labels `job="notes-api"` et `code`.

Elle tient aussi deux journaux du dernier trimestre :
`ops/deployments.jsonl` (un déploiement en production par ligne :
`sha`, `committed_at`, `deployed_at`, `failed`) et `ops/incidents.jsonl` (un
incident par ligne : `deployment_sha`, `started_at`, `resolved_at`).

Le répertoire `challenge/work` contient le projet tel que V10 l'a laissé, avec
ces journaux.

Pratique SSDF visée : PO.4 (définir et appliquer les critères des contrôles de sécurité).

## Objectif

1. `ops/alerts.yaml` porte l'alerte **`NotesApiErrorBudgetBurn`** : elle
   sonne quand le budget brûle **14,4 fois** trop vite, sur une fenêtre longue
   d'une heure et une courte de cinq minutes, et pas quand il s'use lentement.
   Elle renvoie au runbook par son annotation `runbook_url`.
2. `ops/alerts.test.yaml` teste cette alerte avec `promtool test rules`.
3. `ops/runbooks/notes-api-indisponible.md` guide l'astreinte : symptômes,
   diagnostic, remédiation avec retour arrière, escalade. Chaque commande
   `kubectl` vise l'espace de noms et le Deployment réels.
4. `scripts/dora.py <deployments.jsonl> <incidents.jsonl>` écrit un objet
   JSON avec les quatre métriques DORA, arrondies à deux décimales :
   - `deployments_per_week` : déploiements divisés par les semaines écoulées
     entre le premier et le dernier (une semaine au moins) ;
   - `lead_time_hours_median` : médiane de `deployed_at - committed_at`, en
     heures ;
   - `change_failure_rate` : part des déploiements en échec (`failed`) ou
     cause d'un incident ;
   - `recovery_time_hours_median` : médiane de `resolved_at - started_at` des
     incidents, en heures, `null` sans incident (le *Failed Deployment
     Recovery Time*).
5. Le pipeline vérifie et teste l'alerte avec promtool, et calcule les
   métriques ; T-18 passe à `mitigated`.

## Repères

- promtool vit dans l'image `prom/prometheus` : une étape `docker://` avec
  `entrypoint: /bin/promtool`.
- Brûler le budget 14,4 fois trop vite, c'est dépasser 14,4 × 0,5 % = 7,2 %
  d'erreurs : à ce rythme, le budget de 28 jours part en deux jours.
- Deux fenêtres, longue et courte : la longue prouve que la brûlure dure, la
  courte qu'elle dure encore.

## Vérifier

```bash
dsoxlab check capstone-v11-slo-et-dora
```

Cinq contrôles, vingt points chacun. Ils jouent votre pipeline avec act,
soumettent votre alerte à leurs propres séries de requêtes, exécutent votre
script DORA sur des journaux dont ils connaissent les réponses, et relisent le
runbook.
