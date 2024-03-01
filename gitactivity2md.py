# To get started: pip install github; pip install PyGithub
# Tokens here: https://github.com/settings/tokens

# DEBUG:
# import sys
# print(f"Environment:\n{sys.version}\n{sys.path}\n")

import argparse
import errno
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

parser.add_argument('--date', help='Date to get completed tasks for, in ISO format (e.g., 2023-10-07).')
parser.add_argument('--debug', default=False, action='store_true', help='If set will show script debug information.')
parser.add_argument('--range', help='Relative date range to get Git activity for (e.g., "today", "1 day ago", "1 week ago"). Activity is relative to midnight of the day requested.')
parser.add_argument('--repos', nargs='+', help='Repositories to get Git activity for.')

args = parser.parse_args()

DEBUG = args.debug
ARG_DATE = args.date
ARG_RANGE = args.range
ARG_REPOS = args.repos

if ARG_DATE == None and ARG_RANGE == None:
    sys.stderr.write(f"gitactivity2md: --date or --range argument is required\n")
    parser.print_help()
    exit(errno.EINVAL) # Invalid argument error code

if ARG_REPOS == None:
    sys.stderr.write(f"gitactivity2md: --repo or --repos argument is required\n")
    parser.print_help()
    exit(errno.EINVAL) # Invalid argument error code

# #############################################################################
# GLOBALS
# #############################################################################

TODAY_DATETIME = datetime.today().astimezone()
TODAY_TIMESTAMP = datetime(TODAY_DATETIME.year, TODAY_DATETIME.month, TODAY_DATETIME.day).timestamp()

# TODO: limit on number of results returned

OUTPUTTED_COMMITS = []

# #############################################################################
# FUNCTIONS
# #############################################################################

def get_past_datetime(str_days_ago):
    '''
    Returns a datetime for the given date range relative to today.
    today, yesterday, X days ago, X weeks ago, X months ago, X years ago
    '''

    splitted = str_days_ago.split()
    if len(splitted) == 1 and splitted[0].lower() == 'today':
        past_date = TODAY_DATETIME
    elif len(splitted) == 1 and splitted[0].lower() == 'yesterday':
        past_date = TODAY_DATETIME - relativedelta(days=1)
    elif splitted[1].lower() in ['day', 'days', 'd']:
        past_date = TODAY_DATETIME - relativedelta(days=int(splitted[0]))
    elif splitted[1].lower() in ['wk', 'wks', 'week', 'weeks', 'w']:
        past_date = TODAY_DATETIME - relativedelta(weeks=int(splitted[0]))
    elif splitted[1].lower() in ['mon', 'mons', 'month', 'months', 'm']:
        past_date = TODAY_DATETIME - relativedelta(months=int(splitted[0]))
    elif splitted[1].lower() in ['yrs', 'yr', 'years', 'year', 'y']:
        past_date = TODAY_DATETIME - relativedelta(years=int(splitted[0]))
    else:
        return None

    # get midnight of the day requested, to ensure we get all activity on that day
    past_date = past_date.replace(hour=0, minute=0, second=0)

    return past_date

def indent_string(string_to_indent):
    '''
    Indents a multi-line string with tabs.
    '''

    lines = string_to_indent.strip().split("\n")
    indented_lines = ["\t" + line for line in lines]
    indented_string = "\n".join(indented_lines)
    return indented_string

def output_commits(commits, since_datetime, until_datetime = None):
    output = ""
    for commit in commits:
        commit_datetime = commit.commit.author.date
        # convert to local time before doing comparisons
        commit_datetime = commit_datetime.astimezone()
        # only show commits within the given range
        if DEBUG: print(f"{commit.commit.message}")
        if commit_datetime < since_datetime:
            if DEBUG: print(f"  {commit_datetime} < {since_datetime} -> SKIPPING")
            continue            
        if until_datetime:
            if commit_datetime > until_datetime:
                if DEBUG: print(f"  {commit_datetime} > {until_datetime} -> SKIPPING")
                continue
        # ignore merges (quick check: if commit has more than one parent)
        if len(commit.commit.parents) > 1:
            continue
        # don't show commit if we've already shown it
        if commit.commit.sha in OUTPUTTED_COMMITS:
            if DEBUG: print(f"  - SKIPPING {commit.commit.sha}")
            continue
        output += output_commit(commit) + "\n"
    return output

def output_commit(commit):
    output = ""
    commit_message = commit.commit.message
    commit_datetime = commit.commit.author.date.astimezone()
    output += f"- {commit_message} [↗]({commit.commit.html_url})"
    # add a date if the commit is older than today
    if ARG_RANGE:
        if DEBUG: print(f"{commit_datetime} <? {TODAY_DATETIME}")
        if commit_datetime < TODAY_DATETIME:
            output += f" • {commit_datetime.strftime('%Y-%m-%d')}"
    OUTPUTTED_COMMITS.append(commit.commit.sha)
    if DEBUG: print(f"{output}")
    if DEBUG: print(f"    - {commit.commit.sha}")
    if DEBUG: print(f"    - {commit_datetime.astimezone()} -> {commit_datetime.astimezone().timestamp()}")
    if DEBUG: print(f"    - {commit_datetime.isoformat()}")
    if DEBUG: print(f"    - Parent(s): {commit.commit.parents}")
    return output

# #############################################################################
# MAIN
# #############################################################################

sys.stderr.write("Fetching results...\n")

exec_start_time = time.time()

past_datetime = None
if ARG_DATE != None:
    past_datetime = datetime.fromisoformat(ARG_DATE).astimezone()
    past_datetime = past_datetime.replace(hour=0, minute=0, second=0)
    end_datetime = past_datetime.replace(hour=23, minute=59, second=59)
    end_datetime_plus_one = past_datetime.replace(hour=23, minute=59, second=59) + relativedelta(days=1)
    if DEBUG: print(f"Date range: {past_datetime} to {end_datetime}")
elif ARG_RANGE != None:
    past_datetime = get_past_datetime(ARG_RANGE)
    if past_datetime is None:
        sys.stderr.write(f"gitactivity2md: Error: Invalid date range: {ARG_RANGE}\n")
        exit(errno.EINVAL) # Invalid argument error code
    if DEBUG: print(f"Date range ({ARG_RANGE}): On and after {past_datetime}")

# Create a GitHub instance
g = Github(GIT_PERSONAL_ACCESS_TOKEN)
user = g.get_user(GIT_USERNAME)

# #############################################################################

if DEBUG: print(f"ARG_REPOS: {ARG_REPOS}")

for repo_name in ARG_REPOS:
    try:
        if DEBUG: print(f"Getting repo: {repo_name}")
        repo = user.get_repo(repo_name)
    except Exception as e:
        # TODO: sys.stderr.write(f"gitactivity2md: {traceback.print_exc()}")
        print(traceback.print_exc())
        # TODO: find appropriate error code to use here
        exit(1)

    if DEBUG: print(f"Repository: {repo.name}")

    # TODO: option to show dates as headings, or show within each line, or simple (no dates)

    # unfortunately we have to get all pull requests for the repository
    prs = repo.get_pulls(state="all", sort="created", direction="desc")
    for pr in prs:
        if DEBUG: print(f"{pr.number}: {pr.created_at} >=? {past_datetime}")
        if pr.created_at.astimezone() >= past_datetime:
            if ARG_DATE and pr.created_at.astimezone() > end_datetime:
                continue
            print(f"- {repo.name} // [{pr.title}]({pr.html_url})")
            commits = pr.get_commits()
            print(indent_string(output_commits(commits)))

    commits_output = None
    if ARG_DATE:
        commits = repo.get_commits(since=past_datetime, until=end_datetime_plus_one)
        commits_output = output_commits(commits, past_datetime, end_datetime)
    elif ARG_RANGE:
        commits = repo.get_commits(since=past_datetime)
        commits_output = output_commits(commits, past_datetime)
    
    if commits_output:
        if commits_output:
            print(f"- [{repo.name}]({repo.html_url})")
            print(indent_string(commits_output))
        else:
            sys.stderr.write(f"{repo.name}: Nothing in the provided range...\n")

exec_end_time = time.time()
execution_time = exec_end_time - exec_start_time
if DEBUG: print(f"gitactivity2md: Completed in {round(execution_time, 2)}s")

sys.stderr.write(f"gitactivity2md: Completed in {round(execution_time, 2)}s\n")

# TODO: FUTURE? get GitHub issues