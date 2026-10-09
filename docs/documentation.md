# Documentation guide

This document explains where EvoPIE documentation belongs.

## Documentation map

- `README.md`: project identity, short overview, acknowledgement, and links to
  some of the main documentation.
- `docs/how-to-run.md`: local setup and deployment steps.
- `docs/architecture.md`: system design, application workflow, data flow,
  roles, quiz lifecycle, background processing, and deployment shape.
- `docs/user-guide.md`: task-oriented instructions for instructors, students,
  and admins using EvoPIE through the web interface.
- `docs/reference.md`: exact facts, such as role names, quiz statuses,
  commands, environment variables, paths, configuration values, formulas, and
  other factual details.
- `docs/troubleshooting.md`: FAQ-style fixes for common problems.
- `docs/decisions/`: short records explaining important project and
  documentation decisions.

## Updating documentation

When a change alters how EvoPIE works, how it is run, how it is used, or how it
is troubleshot, update the relevant documentation, and _only_ the relevant
documentation/segments of the documentation.

Prefer updating an existing document over creating a new one. Create a new
document only when the information has a clearly different purpose from the
existing documents, and make sure to include it and its description in the
documentation map, and perhaps in the root-level README too if appropriate.
