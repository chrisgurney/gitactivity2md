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
1. Copy token into `.env`

# Examples