#!/usr/bin/env python3
import subprocess
import os
import time
from datetime import datetime

# --- Configuration ---
UPTIME_FILE_PATH = "uptime.log"
GIT_REMOTE_NAME = "origin"
GIT_BRANCH_NAME = "main"
CONFIG_FILE_PATH = "config.txt"

def load_config(config_path):
    """Loads configuration from a file."""
    config = {}
    if not os.path.exists(config_path):
        print(f"Error: Configuration file not found at {config_path}")
        return None
    try:
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        return config
    except (IOError, ValueError) as e:
        print(f"Error reading or parsing config file {config_path}: {e}")
        return None

def run_command(command):
    """Runs a shell command and returns its output."""
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # Suppress errors for commands that are expected to fail if a remote doesn't exist yet.
        if not (command[0] == 'git' and command[1] == 'remote' and command[2] == 'get-url'):
             print(f"Error running command: {' '.join(command)}")
             print(f"Stderr: {e.stderr}")
        return None

def initialize_git_repository(gh_token, github_repo_url):
    """Initializes and configures the git repository for token authentication."""
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

    if not gh_token or gh_token == "your_pat_here" or not github_repo_url or github_repo_url == "https://github.com/your_username/your_repo.git":
        print("Please update GH_TOKEN and GITHUB_REPO_URL in config.txt.")
        return False

    auth_url = github_repo_url.replace("https://", f"https://{gh_token}@")
    
    current_url = run_command(['git', 'remote', 'get-url', GIT_REMOTE_NAME])

    if current_url != auth_url:
        if current_url:
            print(f"Updating remote '{GIT_REMOTE_NAME}' URL for token authentication.")
            run_command(['git', 'remote', 'set-url', GIT_REMOTE_NAME, auth_url])
        else:
            print(f"Adding remote '{GIT_REMOTE_NAME}' for token authentication.")
            run_command(['git', 'remote', 'add', GIT_REMOTE_NAME, auth_url])
    else:
        print(f"Remote '{GIT_REMOTE_NAME}' is already configured correctly.")

    return True

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

    # Pull remote changes before pushing. Use rebase to avoid merge commits.
    print("Pulling remote changes with rebase...")
    pull_command = ['git', 'pull', '--rebase', remote_name, branch_name]
    if run_command(pull_command) is None:
        print("Failed to pull and rebase. A manual merge may be required.")
        # Abort the rebase and reset the commit to try again next time.
        run_command(['git', 'rebase', '--abort'])
        run_command(['git', 'reset', 'HEAD~1'])
        return False

    push_command = ['git', 'push', remote_name, branch_name]
    if run_command(push_command) is None:
        print("Failed to push changes to GitHub. Trying to set upstream branch.")
        set_upstream_command = ['git', 'push', '--set-upstream', remote_name, branch_name]
        if run_command(set_upstream_command) is None:
            print("Failed to set upstream and push.")
            return False

    print("Successfully pushed changes to GitHub.")
    return True

def main():
    """
    Continuously retrieves uptime, saves it to a file, and commits it to git.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    config = load_config(CONFIG_FILE_PATH)
    if not config:
        return

    gh_token = config.get("GH_TOKEN")
    github_repo_url = config.get("GITHUB_REPO_URL")

    if not initialize_git_repository(gh_token, github_repo_url):
        return

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
