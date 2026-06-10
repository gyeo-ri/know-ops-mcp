# Knowledge-base style guide

Conventions that keep entries consistent across projects and sessions. Read this
before creating a new entry. When in doubt, match what already exists under the
same project.

## 1. Key namespace

`knowledge_key` is lowercase letters, digits, hyphens, and `/` for hierarchy.

- **Project knowledge** lives under `projects/<project>/<doc-type>`.
  e.g. `projects/lge-social/overview`, `projects/gyeori-blog/architecture`
- **Sub-areas** of a large project get one more level:
  `projects/<project>/<area>/<doc>` — e.g. `projects/lge-social/airflow/todo`.
- **Project name is stable and canonical.** Pick one kebab-case name per project
  and never split the same project across two names or two roots (the classic
  failure: `projects/lge-social/*` *and* a top-level `lge-social-data-pipeline/*`).
  Before creating, `list_knowledge(prefix='projects/')` and reuse the existing name.
- Non-project knowledge may use a flat topic key (e.g. `python-async-patterns`).

## 2. One doc per concern

Each concern has exactly one canonical key. Don't create a second entry that
overlaps an existing one — update the existing entry instead. The standard
per-project docs and what each holds:

| doc-type | holds |
|---|---|
| `overview` | identity/purpose, stack summary, repo structure, current state |
| `architecture` | technical depth: components, data flow, storage, auth, deploy |
| `design-decisions` | decision log: problem → options → decision → rationale |
| `history` | condensed chronological milestone log |
| `session` | one work session's log (key `…/session-YYYY-MM-DD`) |
| `roadmap` | planned phases / upcoming work |
| `todo` | open tasks |
| `runbook` | operational procedures / SOPs (incl. secrets handling) |
| `note` | freeform topic note that fits no type above |

`overview` vs `architecture`: keep `overview` scannable (what it is, where things
are, what's done); push deep technical detail into `architecture`. When an
overview section grows large, promote it to its own doc.

## 3. Frontmatter

`created` and `updated` are managed by the server — never set them by hand.
You control:

- **title** — human-readable, specific.
- **description** — ONE line, what the entry is and why it matters. This is what
  other sessions scan to decide relevance, so make it informative, not generic.
- **tags** — see below.

## 4. Tag vocabulary (controlled)

Keep tags few and consistent so filtering works. Each entry gets:

- exactly one **project tag** = the project name (e.g. `lge-social`), and
- exactly one **type tag** = the doc-type (`overview`, `architecture`,
  `design`, `history`, `session`, `roadmap`, `todo`, `runbook`, `note`), and
- optionally a few **tech tags** from a small shared set
  (`airflow`, `terraform`, `aws`, `lambda`, `react`, `fastapi`, ...).

Lowercase kebab-case. Don't invent synonyms — use `overview`, not also
`project-overview`; use `design`, not `design-decisions` *and* `decisions`.

## 5. Keep entries true to their source

When you revise an entry, verify claims against the source of truth (the repo,
the code, the infra) rather than copying stale prose. A later `updated` date on a
wrong entry is worse than an honest old one. If two entries disagree, reconcile
them — don't leave both.

## 6. Session log policy

Log a work session as `projects/<project>/session-YYYY-MM-DD`. Sessions are a raw
log; durable outcomes (decisions, milestones) belong in `design-decisions` or
`history`. When sessions pile up (rule of thumb: more than ~5, or when a
milestone ships), fold their durable points into `history` and let the raw
session entries age out.
