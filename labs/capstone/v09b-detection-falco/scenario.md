# V9b: seeing when someone got in

## Situation

V9 closed notes-api: restricted pod, isolated network. These protections
reduce what an attacker can do, but none says **when** they got in. A shell
opened in the container, or a file changed in the running code, would go by
without a word.

On the `falco-1.lab` machine, an Ubuntu 24.04, notes-api runs in Docker under
the name `notes-api`, and **Falco 0.45.0** watches it with its modern eBPF
probe. The setup already has every alert written, in JSON, to
`/var/log/falco/events.json`. What is missing are the rules that say what must
never happen in notes-api.

SSDF practice targeted: RV.1 (identify and confirm vulnerabilities on an ongoing basis).

## Goal

Write `/etc/falco/rules.d/notes-api.yaml`, loaded by Falco on every start:

1. a **shell** opened in the notes-api container raises an alert of level
   **WARNING** at least, which cites the container and the **command line**;
2. a **write under /app** in the notes-api container raises an alert of level
   **ERROR** at least, which cites the container and the **file**;
3. the normal activity of notes-api (its server, its Python health probe) and
   a shell in **another** container raise **no** alert from your rules;
4. the rules pass `falco -V` and **survive** a restart of Falco.

## Pointers

- `dsoxlab run` connects you to `falco-1.lab`. `sudo docker exec notes-api sh`
  opens the shell your rules must see.
- The `spawned_process` and `open_write` macros come from the default rules,
  `/etc/falco/falco_rules.yaml`: validating your file alone fails, validate
  both, `falco -V /etc/falco/falco_rules.yaml -V <your file>`.
- `container.name`, `proc.name`, `proc.cmdline`, `fd.name` and `user.name` are
  the useful fields. A rule's output only carries the fields it cites.
- The service is called `falco-modern-bpf.service`.

## Check

```bash
dsoxlab check capstone-v09b-detection-falco
```

Five checks, twenty points each. They trigger a shell and a write in notes-api
themselves, then what must trigger nothing, and read the alerts of your rules
only in `/var/log/falco/events.json`.
