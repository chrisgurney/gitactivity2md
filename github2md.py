# To get started: pip install github; pip install PyGithub
# Tokens here: https://github.com/settings/tokens

import argparse
import os
import traceback
from datetime import datetime
from dateutil.relativedelta import *
from dotenv import load_dotenv
from github import Github

# #############################################################################
# CONFIGURATION
# #############################################################################

load_dotenv()

# get configuration from .env
GIT_PERSONAL_ACCESS_TOKEN = os.getenv("GIT_PERSONAL_ACCESS_TOKEN")
GIT_USERNAME = os.getenv("GIT_USERNAME")

# #############################################################################
# CLI ARGUMENTS
# #############################################################################

parser = argparse.ArgumentParser(description='Script that returns a list of PRs and commits in markdown.')

parser.add_argument('--debug', default=False, action='store_true', help='If set will show script debug information')
parser.add_argument('--range', help='Relative date range to get Git activity for (e.g., "today", "1 day ago", "1 week ago"). Activity is relative to midnight of the day requested.')
parser.add_argument('--repo', help='')

# TODO: accept a list of repo names:
    # https://stackoverflow.com/questions/15753701/how-can-i-pass-a-list-as-a-command-line-argument-with-argparse
# TODO repo arg default: get all public repos for user, otherwise?

args = parser.parse_args()

DEBUG = args.debug
ARG_RANGE = args.range
ARG_REPO = args.repo

# #############################################################################
# GLOBALS
# #############################################################################

TODAY = datetime.today()

# TODO: limit on number of results returned

# #############################################################################
# FUNCTIONS
# #############################################################################

def get_past_time(str_days_ago):
    '''
    Returns a timestamp for the given date range relative to today.
    today, yesterday, X days ago, X weeks ago, X months ago, X years ago
    '''

    splitted = str_days_ago.split()
    past_time = ""
    if len(splitted) == 1 and splitted[0].lower() == 'today':
        past_time = TODAY.timestamp()
    elif len(splitted) == 1 and splitted[0].lower() == 'yesterday':
        past_date = TODAY - relativedelta(days=1)
        past_time = past_date.timestamp()
    elif splitted[1].lower() in ['day', 'days', 'd']:
        past_date = TODAY - relativedelta(days=int(splitted[0]))
        past_time = past_date.timestamp()
    elif splitted[1].lower() in ['wk', 'wks', 'week', 'weeks', 'w']:
        past_date = TODAY - relativedelta(weeks=int(splitted[0]))
        past_time = past_date.timestamp()
    elif splitted[1].lower() in ['mon', 'mons', 'month', 'months', 'm']:
        past_date = TODAY - relativedelta(months=int(splitted[0]))
        past_time = past_date.timestamp()
    elif splitted[1].lower() in ['yrs', 'yr', 'years', 'year', 'y']:
        past_date = TODAY - relativedelta(years=int(splitted[0]))
        past_time = past_date.timestamp()
    else:
        return("Wrong date range format")

    # get midnight of the day requested, to ensure we get all tasks
    past_date = datetime.fromtimestamp(float(past_time))
    past_date = datetime(past_date.year, past_date.month, past_date.day)
    past_time = past_date.timestamp()

    return past_time   

# #############################################################################
# MAIN
# #############################################################################

past_time = None
if ARG_RANGE != None:
    past_time = get_past_time(ARG_RANGE)
    if past_time == "Wrong date range format":
        print("Error: " + past_time + ": " + ARG_RANGE)
        exit()
    if DEBUG: print("\nDATE:\n{} -> {}".format(ARG_RANGE,past_time))

# Create a GitHub instance
g = Github(GIT_PERSONAL_ACCESS_TOKEN)
user = g.get_user(GIT_USERNAME)

# #############################################################################

# TODO: if multiple repos provided, iterate over them

try:
    repo = user.get_repo(ARG_REPO)
except Exception as e:
    print(traceback.print_exc())
    exit()

if DEBUG: print(f"Repository: {repo.name}")

# TODO: get PRs and list commits under each PR

# List pull requests for the repository
prs = repo.get_pulls(state="all", sort="created", direction="desc")

# TODO: show PRs, and commits under each PR
for pr in prs:
    print(f"PR #{pr.number}: {pr.title}")
    pr_commits = pr.get_commits()
    # TODO: list PR commits

# TODO: show dates as headings, or option to show within each line (like things2md)

results = 0
repo_commits = repo.get_commits()
if repo_commits:
    for repo_commit in repo_commits:
        commit_message = repo_commit.commit.message
        commit_datetime = repo_commit.commit.author.date
        # only show commits up to the given range (if provided)
        if past_time and commit_datetime.timestamp() < past_time:
            break   
        print(f"- {repo.name} // {commit_message}")
        if DEBUG: print(f"  - {commit_datetime.astimezone()} -> {commit_datetime.astimezone().timestamp()}")
        results += 1

if results == 0:
    print(f"No activity for the provided range: {ARG_RANGE}")
    exit(0)

# TODO: FUTURE? get GitHub issues