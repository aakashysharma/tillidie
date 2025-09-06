#!/usr/bin/env python3
import subprocess
import os
import time
from datetime import datetime

# --- Configuration ---
# The path to the file where the uptime output will be stored.
# This path is relative to the script's location.
UPTIME_FILE_PATH = "uptime.log"
GIT_REMOTE_NAME = "origin"
GIT_BRANCH_NAME = "main"

# --- Git Authentication ---
# This script uses a GitHub Personal Access Token (PAT) for authentication.
# 1. Create a PAT with the `repo` scope.
#    - Go to https://github.com/settings/tokens/new
# 2. Set the PAT as an environment variable named `GH_TOKEN`.
#    - export GH_TOKEN="your_pat_here"
# 3. Configure your git remote URL to use the PAT.
#    - git remote set-url <remote_name> https://<your_username>:${GH_TOKEN}@github.com/<your_username>/<your_repo>.git
#
# For more information, see:
# https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token

def run_command(command):
    """Runs a shell command and returns its output."""
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(command)}")
        print(f"Stderr: {e.stderr}")
        return None

def get_uptime():
    """Retrieves the system uptime."""
    return run_command(['uptime'])

def write_uptime_to_file(file_path, uptime_output):
    """Appends the uptime to the specified file."""
    try:
        with open(file_path, 'a') as f:
            f.write(f"{datetime.now().isoformat()}: {uptime_output}\n")
        print(f"Successfully wrote uptime to {file_path}")
        return True
    except IOError as e:
        print(f"Error writing to file {file_path}: {e}")
        return False

def git_commit_and_push(file_path, remote_name, branch_name):
    """Stages, commits, and pushes the specified file to git."""
    # Stage the file
    run_command(['git', 'add', file_path])

    # Check for changes to commit
    git_status = run_command(['git', 'status', '--porcelain'])
    if not git_status:
        print("No changes to commit.")
        return True

    # Commit the file
    commit_message = "feat: record system uptime"
    commit_output = run_command(['git', 'commit', '-m', commit_message])
    if commit_output is None:
        print("Failed to create git commit.")
        return False
    print("Successfully created git commit.")
    print(commit_output)

    # Push the commit
    push_command = ['git', 'push', remote_name, branch_name]
    push_output = run_command(push_command)
    if push_output is None:
        print("Failed to push changes to GitHub.")
        return False

    print("Successfully pushed changes to GitHub.")
    return True

def main():
    """
    Continuously retrieves uptime, saves it to a file, and commits it to git.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    abs_uptime_file_path = os.path.join(script_dir, UPTIME_FILE_PATH)
    os.chdir(script_dir)

    while True:
        print(f"\n--- {datetime.now().isoformat()} ---")
        uptime_output = get_uptime()
        if uptime_output:
            print(f"Uptime: {uptime_output}")
            if write_uptime_to_file(abs_uptime_file_path, uptime_output):
                git_commit_and_push(UPTIME_FILE_PATH, GIT_REMOTE_NAME, GIT_BRANCH_NAME)

        print("Waiting for 5 minutes before the next run...")
        time.sleep(300)

if __name__ == "__main__":
    main()
