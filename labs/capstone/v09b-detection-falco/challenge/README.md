# Challenge: runtime detection

5 tasks, 100 points, 50 minutes.

The work happens on `falco-1.lab`: you write
`/etc/falco/rules.d/notes-api.yaml`.

### Task 1: the rules are valid and Falco runs (20 pts)

The file passes `falco -V` with the default rules, the `falco-modern-bpf`
service runs, and so does the notes-api container.

### Task 2: a shell in notes-api raises an alert (20 pts)

An alert from your rules, of level WARNING at least, cites the container and
the command run.

### Task 3: a write into the code raises an alert (20 pts)

A file created under `/app/src` raises an alert of level ERROR at least,
which cites the file.

### Task 4: normal activity raises nothing (20 pts)

The notes-api health probe and a shell in another container raise no alert
from your rules.

### Task 5: the rules survive a restart (20 pts)

After `systemctl restart falco-modern-bpf`, the shell in notes-api is still
detected.
