---
name: data-engineering-learnings
description: >
  Use this skill when working inside the data-engineering-learnings repository — a
  shared learning repo where each learner has their own branch for session
  exercises and KPI tracking, connected to Databricks via Git Repos. Trigger when
  the user asks to set up a learner branch, scaffold a learner folder, create or
  update a KPI tracker, add a session exercise, review a learner's push/diff, or
  answer questions about the repo's branching model and Databricks Git sync.
---

# Data Engineering Learnings Skill

Governs how work is created and organized inside the `data-engineering-learnings`
repo. This repo backs a Databricks training cohort. Every learner has a personal
branch, does session exercises, and tracks KPIs.

## Core facts about this repo

- `main` is protected and holds only shared exercise templates and resources.
- Each learner works in `learner/<name>` (for example `learner/sachindra`).
- Learner work lives in `learners/<name>/` with `exercises/` and `kpis.md`.
- The repo is synced to Databricks through **Repos** (Git integration). Changes
  can be committed from the Databricks Repos UI or from local Git.

## Branch naming

Always use `learner/<name>`, lowercase, hyphenated if the name has spaces.
Never suggest pushing to `main` directly. Any path to `main` is a pull request.

## When asked to scaffold a new learner

Create this structure on their branch:

```
learners/<name>/
├── exercises/
│   └── .gitkeep
└── kpis.md
```

Seed `kpis.md` from the KPI template below.

## KPI tracker template

Use this exact table when creating or resetting a learner's `kpis.md`:

```markdown
# KPIs — <Learner Name>

| KPI | Target | Current | Notes |
|-----|--------|---------|-------|
| Sessions attended | — | 0 | Out of total sessions |
| Exercises completed | — | 0 | Per session |
| Certification progress | — | Not started | Databricks cert module status |
| Notebook runs / clusters used | — | 0 | Hands-on activity |
| Peer review contributions | — | 0 | PRs reviewed |

_Last updated: <date>_
```

When updating KPIs, only touch the Current/Notes/Last updated fields unless the
user asks to change targets.

## Session exercise conventions

- Place completed session work under `learners/<name>/exercises/session-NN/`.
- Commit message format: `session-NN: <short description>` (for example
  `session-03: completed ETL exercise`).
- Never write into another learner's folder.
- Shared starter templates come from the top-level `exercises/session-NN/` folder;
  copy from there into the learner folder, do not edit the shared template.

## When reviewing a learner's diff or push

- Confirm the work is inside their own `learners/<name>/` folder.
- Check the commit message follows the `session-NN:` convention.
- Flag any committed credentials, tokens, or `.env` files immediately.
- Confirm no changes touch `main`-only paths (`exercises/`, `resources/`, README).

## Hard rules

1. Never push or merge directly to `main` — always a reviewed PR.
2. Never commit secrets, tokens, or personal access keys.
3. Keep every learner's work isolated to their own folder and branch.
4. Preserve the KPI table structure; do not restyle it into prose.
