# data-engineering-learnings

A shared repository for the Databricks learning cohort. Each learner works in their own branch, pushing session exercises and tracking KPIs. This repo is connected to Databricks via Repos (Git integration), so notebooks and code sync directly between the workspace and Git.

## What lives here

- **Session exercises** completed during and after each training session.
- **Individual learner branches** where all work is committed and pushed.
- **KPIs** tracked per learner to measure progress across the program.

## Repository structure

```
data-engineering-learnings/
├── README.md
├── exercises/            # Shared exercise templates and session starters
│   ├── session-01/
│   ├── session-02/
│   └── ...
├── learners/            # Per-learner folders (created on their own branch)
│   └── <learner-name>/
│       ├── exercises/   # Completed session work
│       └── kpis.md      # Individual KPI tracker
└── resources/           # Datasets, cheat sheets, reference material
```

## Branching model

- `main` — protected. Holds exercise templates and shared resources. No direct pushes.
- `learner/<name>` — each learner's personal branch (for example `learner/sachindra`). All individual work goes here.

Learners never push to `main` directly. Changes reach `main` only through a reviewed pull request.

## Getting started

### 1. Clone the repo

```bash
git clone https://github.com/<org>/data-engineering-learnings.git
cd data-engineering-learnings
```

### 2. Create your branch

```bash
git checkout -b learner/<your-name>
git push -u origin learner/<your-name>
```

### 3. Connect in Databricks (optional)

Connecting through Databricks Repos is optional. You can also do all your work locally in your own IDE (VS Code, PyCharm, etc.) and push with regular Git. Use whichever workflow you prefer.

To connect via Databricks:

1. In your Databricks workspace, go to **Repos** and click **Add Repo**.
2. Paste the HTTPS Git URL of this repository.
3. Once cloned, switch to your branch (`learner/<your-name>`) from the branch dropdown in the Repos UI.
4. Work on notebooks inside your `learners/<your-name>/` folder.

### 4. Push your work

From the Databricks Repos UI, commit and push directly. Or from local Git:

```bash
git add .
git commit -m "session-03: completed ETL exercise"
git push
```

## KPI tracking

Each learner maintains a `kpis.md` in their folder. Suggested metrics:

| KPI                           | Target | Notes                         |
| ----------------------------- | ------ | ----------------------------- |
| Sessions attended             | —      | Out of total sessions         |
| Exercises completed           | —      | Per session                   |
| Certification progress        | —      | Databricks cert module status |
| Notebook runs / clusters used | —      | Hands-on activity             |
| Peer review contributions     | —      | PR reviews given              |

Update your KPIs at the end of each session and push them with your exercise commits.

## Rules

1. Work only in your own `learner/<name>` branch.
2. Do not push directly to `main`.
3. Keep exercises inside your `learners/<your-name>/` folder to avoid collisions.
4. Write clear commit messages tied to the session (for example `session-04: streaming exercise`).
5. Never commit credentials, tokens, or personal access keys.

## Support

Raise a GitHub Issue for repo or access problems. For Databricks workspace or cluster issues, contact the program lead.
