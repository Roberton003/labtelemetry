# Public Documentation And Security Policy

This repository keeps public documentation focused on product usage, architecture, API, and operation.

The following content is intentionally excluded from the public repository:

- private planning records;
- work-session records;
- internal workflow notes;
- career strategy material;
- private appendices and research excerpts;
- non-public decision logs;
- local environment files and secrets.

## Secret Handling

Do not commit:

- `.env`;
- production secrets;
- tokens;
- private hostnames;
- private datasets;
- personal notes;
- internal work logs.

Use `.env.example` for safe development defaults only.
