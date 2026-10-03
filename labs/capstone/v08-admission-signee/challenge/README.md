# Challenge: signed admission

5 tasks, 100 points, 50 minutes.

The project is in `challenge/work`. You create the policies in
`deploy/policies/`, and you evolve `threat-model.yml`.

### Task 1: an image signed by the platform is admitted (20 pts)

In `notes-api`, an image from the internal registry signed with the key of
`deploy/signing/cosign.pub` is admitted.

### Task 2: an unsigned image is refused (20 pts)

The Pod is refused, and a Deployment that names that image is refused at
creation.

### Task 3: an image signed with another key is refused (20 pts)

A signature is not enough: it must come from the platform key.

### Task 4: an image from another registry is refused in notes-api (20 pts)

A Docker Hub image is refused in `notes-api`, and the same image is still
admitted in `default`.

### Task 5: the policies block, the model is up to date (20 pts)

The policies are `ValidatingPolicy` and `ImageValidatingPolicy` in `Deny`,
without `failurePolicy: Ignore`, the platform key is in them, and T-15 is
`mitigated` with its evidence.
