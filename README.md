Script that fetches a list of PRs and commits.

# Installation

`pip3 install -r requirements.txt`

Copy `.env.example` to `.env` and update with your Git configuration.

## GitHub Tokens

1. Create a token in GitHub: _Settings > Developer > Personal access tokens > Fine-grained token_
1. Provide read-only access to whatever repos you want to report on. Settings I used:
    - Contents -> read-only
    - Metadata -> read-only (automatically set)
    - Pull Requests -> read-only
1. Copy token into the `.env` into the `GIT_PERSONAL_ACCESS_TOKEN` variable

# Usage

Run without any parameters to see the full list of arguments available:

```
--debug               If set will show script debug information.
--range RANGE         Relative date range to get Git activity for (e.g., "today", "1 day ago", "1
                      week ago"). Activity is relative to midnight of the day requested.
--repo REPO           Repository to get Git activity for.
--repos REPOS [REPOS ...]
                      Repositories to get Git activity for.
```

The `--range` parameter is required, at a minimum.

# Examples

Show PRs and individual commits under two repos, that were checked in today.
```
python3 github2md.py --repos myrepo myotherrepo --range "today"
```

Show PRs and individual commits under one repo, that were checked in over the last couple days.
```
python3 github2md.py --repo myrepo --range "1 day ago"
```