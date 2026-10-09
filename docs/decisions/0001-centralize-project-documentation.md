# 0001. Centralize project documentation

## Status

Accepted

## Context

EvoPIE documentation was spread across the README, text files, a PDF manual,
and the GitHub wiki. That made it harder to know where current project
knowledge should live.

## Decision

Keep the main project documentation as Markdown files in this repository. Use
the README as a map to the documentation, and organize the docs by purpose.

## Consequences

Project knowledge can be updated in the same branch as code changes. Historical
manual and wiki content should be migrated into the Markdown documentation
before those sources are removed or ignored.
