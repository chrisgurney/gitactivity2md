# To get started: pip install github; pip install PyGithub
# Tokens here: https://github.com/settings/tokens

# import sys
# print(f"Environment:\n{sys.version}\n{sys.path}\n")

import argparse
import os
import sys
import time
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
parser.add_argument('--repo', help='Repository to get Git activity for')

# TODO: implement support for multiple repos
# parser.add_argument('--repos', nargs='+', help='') 

args = parser.parse_args()

DEBUG = args.debug
ARG_RANGE = args.range
ARG_REPO = args.repo

if ARG_RANGE == None and (ARG_REPO == None):
    parser.print_help()
    exit(0)

# #############################################################################
# GLOBALS
# #############################################################################

TODAY = datetime.today()

# TODO: limit on number of results returned

OUTPUTTED_COMMITS = []

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

def indent_string(string_to_indent):
    '''
    Indents a multi-line string with tabs.
    '''

    lines = string_to_indent.strip().split("\n")
    indented_lines = ["\t" + line for line in lines]
    indented_string = "\n".join(indented_lines)
    return indented_string

def output_commits(commits):
    output = ""
    results = 0
    for commit in commits:
        commit_datetime = commit.commit.author.date
        # only show commits up to the given range (if provided)
        if past_time and commit_datetime.timestamp() < past_time:
            break
        # ignore merges (quick check: if commit has more than one parent)
        if len(commit.commit.parents) > 1:
            continue
        # don't show commit if we've already shown it
        if commit.commit.sha in OUTPUTTED_COMMITS:
            if DEBUG: print(f"  - SKIPPING {commit.commit.sha}")
            continue
        output += output_commit(commit) + "\n"
        results += 1
    if results == 0:
        sys.stderr.write(f"No commits to show\n")
        exit(0)
    return output

def output_commit(commit):
    output = ""
    commit_message = commit.commit.message
    commit_datetime = commit.commit.author.date
    output += f"- {commit_message}"
    OUTPUTTED_COMMITS.append(commit.commit.sha)
    if DEBUG: print(f"    - {commit.commit.sha}")
    if DEBUG: print(f"    - {commit_datetime.astimezone()} -> {commit_datetime.astimezone().timestamp()}")
    if DEBUG: print(f"    - Parent(s): {commit.commit.parents}")
    return output

# #############################################################################
# MAIN
# #############################################################################

sys.stderr.write("github2md: Fetching results...\n")

start_time = time.time()

past_time = None
past_datetime = None
if ARG_RANGE != None:
    past_time = get_past_time(ARG_RANGE)
    if past_time == "Wrong date range format":
        print("Error: " + past_time + ": " + ARG_RANGE)
        exit()
    past_datetime = datetime.fromtimestamp(past_time)
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

# TODO: show dates as headings, or option to show within each line (like things2md)

# list pull requests for the repository
prs = repo.get_pulls(state="all", sort="created", direction="desc")
for pr in prs:
    if DEBUG: print(f"{pr.number}: {pr.created_at.timestamp()} >? {past_time}")
    if pr.created_at.timestamp() > past_time:
        print(f"- [{pr.title}]({pr.html_url})")
        commits = pr.get_commits()
        commits_output = output_commits(commits)
        commits_indented = indent_string(commits_output)
        print(commits_indented)

commits = repo.get_commits(since=past_datetime)
if commits:
    print(f"{repo.name}")
    print(output_commits(commits), end="")

end_time = time.time()
execution_time = end_time - start_time
if DEBUG: print(f"github2md: Completed in {round(execution_time, 4)} seconds.")

sys.stderr.write(f"Completed in {round(execution_time, 4)} seconds\n")

# TODO: FUTURE? get GitHub issues