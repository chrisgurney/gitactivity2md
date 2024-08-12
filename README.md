Script that fetches a list of PRs and commit in Markdown format.

# Installation

```zsh
pip3 install -r requirements.txt
```
...or if using a virtual environment:
```zsh
cd /path/to/things2md/
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

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
--date DATE           Date to get completed tasks for, in ISO format (e.g., 2023-10-07).
--range RANGE         Relative date range to get Git activity for (e.g., "today", "1 day ago", "1
                      week ago"). Activity is relative to midnight of the day requested.
--repos REPOS [REPOS ...]
                      Repositories to get Git activity for.
```

The (`--date` or `--range`) and `--repos` parameters are required, at a minimum.

Notes:

- Merges are ignored (check is based on whether commit has more than one parent).

# Examples

Show PRs and individual commits under a single repo, that was checked in on 2023-02-27.
```zsh
python3 gitactivity2md.py --repos myrepo --date 2023-02-27
```
Or if using a virtual environment:
```zsh
source /path/to/gitactivity2md/.venv/bin/activate && python3 gitactivity2md.py --repos myrepo --date 2023-02-27
```

Show PRs and individual commits under two repos, that were checked in since yesterday.
```zsh
python3 gitactivity2md.py --repos myrepo myotherrepo --range "yesterday"
```