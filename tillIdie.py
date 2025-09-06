#!/usr/bin/env python3
import subprocess
import os
import time
from datetime import datetime

# --- Configuration ---
# WARNING: Hardcoding your PAT is a significant security risk.
# It is strongly recommended to use environment variables instead.
# If this code is ever shared or made public, your token will be exposed.
GH_TOKEN = "your_pat_here"  # Replace with your GitHub Personal Access Token
GITHUB_REPO_URL = "https://github.com/your_username/your_repo.git"  # Replace with your repository URL

UPTIME_FILE_PATH = "uptime.log"
GIT_REMOTE_NAME = "origin"
GIT_BRANCH_NAME = "main"


def run_command(command):
    """Runs a shell command and returns its output."""
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(command)}")
        print(f"Stderr: {e.stderr}")
        return None

def initialize_git_repository():
    """Initializes the git repository if it's not already set up."""
    if not os.path.isdir('.git'):
        run_command(['git', 'init'])
        print("Initialized empty Git repository.")

    gitignore_path = '.gitignore'
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, 'w') as f:
            f.write("# Ignore all files\n*\n# Un-ignore the uptime log\n!uptime.log\n")
        print("Created .gitignore to only track uptime.log")
        run_command(['git', 'add', gitignore_path])
        run_command(['git', 'commit', '-m', 'feat: Add .gitignore'])
        print("Committed .gitignore.")

    remotes = run_command(['git', 'remote'])
    if not remotes or GIT_REMOTE_NAME not in remotes.split():
        if GH_TOKEN == "your_pat_here" or GITHUB_REPO_URL == "https://github.com/your_username/your_repo.git":
            print("Please update GH_TOKEN and GITHUB_REPO_URL in the script.")
            return
        auth_url = GITHUB_REPO_URL.replace("https://", f"https://{GH_TOKEN}@")
        run_command(['git', 'remote', 'add', GIT_REMOTE_NAME, auth_url])
        print(f"Added remote '{GIT_REMOTE_NAME}'.")

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
    run_command(['git', 'add', file_path])

    git_status = run_command(['git', 'status', '--porcelain'])
    if not git_status:
        print("No changes to commit.")
        return True

    commit_message = "feat: record system uptime"
    commit_output = run_command(['git', 'commit', '-m', commit_message])
    if commit_output is None:
        print("Failed to create git commit.")
        return False
    print("Successfully created git commit.")

    push_command = ['git', 'push', remote_name, branch_name]
    push_output = run_command(push_command)
    if push_output is None:
        print("Failed to push changes to GitHub.")
        # Try to set the upstream branch on the first push
        if "has no upstream branch" in push_output:
            run_command(['git', 'push', '--set-upstream', remote_name, branch_name])
        return False

    print("Successfully pushed changes to GitHub.")
    return True

def main():
    """
    Continuously retrieves uptime, saves it to a file, and commits it to git.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    initialize_git_repository()

    abs_uptime_file_path = os.path.join(script_dir, UPTIME_FILE_PATH)

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
