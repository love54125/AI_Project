import os
import requests
import json
import subprocess
import shutil
import stat

def remove_readonly(func, path, excinfo):
    """
    Error handler for shutil.rmtree.
    If the error is due to a read-only file, it changes the permission and re-attempts.
    """
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)

# ==============================================================================
# --- GitHub Tools ---
# ==============================================================================

def get_github_pat():
    """Reads the GitHub PAT from the environment variable."""
    pat = os.environ.get("GITHUB_PAT")
    if not pat:
        raise ValueError("GITHUB_PAT environment variable not set.")
    return pat

def read_repo_info(owner: str, repo: str):
    """
    Gets the basic information for a specified GitHub repository.
    """
    pat = get_github_pat()
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {
        "Authorization": f"token {pat}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Gemini-Agent"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {e}"}

def create_github_issue(owner: str, repo: str, title: str, body: str, labels: list = None):
    """
    Creates a new issue in a specified GitHub repository.
    """
    pat = get_github_pat()
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    headers = {
        "Authorization": f"token {pat}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Gemini-Agent"
    }
    data = {
        "title": title,
        "body": body,
        "labels": labels if labels is not None else []
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {e}"}

# ==============================================================================
# --- Google Task Tools ---
# ==============================================================================

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

def get_google_credentials():
    """
    Refreshes and returns Google API credentials from the token file.
    """
    token_file = 'F:\\Project\\GeminiProject\\google_task_token.json'
    creds = None
    
    # The file stores the user's access and refresh tokens.
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, ['https://www.googleapis.com/auth/tasks'])
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save the refreshed credentials back to the file
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
                return creds
            except Exception as e:
                raise RuntimeError(f"Failed to refresh Google token: {e}")
        else:
            raise RuntimeError(
                "Google credentials are not valid and cannot be refreshed. "
                "Please re-run the initial authorization process."
            )
    return creds

def list_google_tasks(task_list_id: str = '@default', show_completed: bool = False):
    """
    Lists tasks from a specified Google Task list.
    """
    try:
        creds = get_google_credentials()
        service_url = f"https://tasks.googleapis.com/tasks/v1/lists/{task_list_id}/tasks"
        
        params = {
            'showCompleted': show_completed
        }
        headers = {
            'Authorization': f'Bearer {creds.token}'
        }
        
        response = requests.get(service_url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
        
    except (RuntimeError, requests.exceptions.RequestException) as e:
        return {"error": f"Failed to list Google tasks: {e}"}

def create_google_task(title: str, task_list_id: str = '@default', notes: str = None):
    """
    Creates a new task in a specified Google Task list.
    """
    try:
        creds = get_google_credentials()
        service_url = f"https://tasks.googleapis.com/tasks/v1/lists/{task_list_id}/tasks"
        
        headers = {
            'Authorization': f'Bearer {creds.token}',
            'Content-Type': 'application/json'
        }
        
        task_data = {
            'title': title,
        }
        if notes:
            task_data['notes'] = notes
        
        response = requests.post(service_url, headers=headers, json=task_data)
        response.raise_for_status()
        return response.json()
        
    except (RuntimeError, requests.exceptions.RequestException) as e:
        return {"error": f"Failed to create Google task: {e}"}

def complete_google_task(task_id: str, task_list_id: str = '@default'):
    """
    Marks a Google Task as completed.
    """
    try:
        creds = get_google_credentials()
        service_url = f"https://tasks.googleapis.com/tasks/v1/lists/{task_list_id}/tasks/{task_id}"
        
        headers = {
            'Authorization': f'Bearer {creds.token}',
            'Content-Type': 'application/json'
        }
        
        # To mark a task as complete, you update its status.
        # The API uses PATCH for updates.
        task_data = {
            'status': 'completed'
        }
        
        response = requests.patch(service_url, headers=headers, json=task_data)
        response.raise_for_status()
        return response.json()
        
    except (RuntimeError, requests.exceptions.RequestException) as e:
        return {"error": f"Failed to complete Google task: {e}"}

# ==============================================================================
# --- Git Tools ---
# ==============================================================================

def clone_repository(repo_url: str, local_path: str):
    """
    Clones a public repository to a local path.
    """
    if os.path.exists(local_path):
        return {"error": f"Directory already exists: {local_path}"}
    
    try:
        # Using subprocess for more control over git commands
        result = subprocess.run(
            ["git", "clone", repo_url, local_path],
            capture_output=True, text=True, check=True
        )
        return {"status": "success", "output": result.stdout}
    except FileNotFoundError:
        return {"error": "Git command not found. Is Git installed and in your PATH?"}
    except subprocess.CalledProcessError as e:
        return {"error": f"Git clone failed: {e.stderr}"}

def commit_and_push_changes(local_path: str, message: str, branch: str):
    """
    Adds all changes, commits them, and pushes to the remote branch.
    """
    try:
        # Git Add
        add_result = subprocess.run(
            ["git", "add", "."], cwd=local_path, capture_output=True, text=True, check=True
        )
        
        # Git Commit
        commit_result = subprocess.run(
            ["git", "commit", "-m", message], cwd=local_path, capture_output=True, text=True, check=True
        )
        
        # Git Push
        # This requires authentication to be set up in the environment (e.g., via a credential manager)
        push_result = subprocess.run(
            ["git", "push", "origin", branch], cwd=local_path, capture_output=True, text=True, check=True
        )
        
        return {"status": "success", "output": push_result.stdout}
        
    except FileNotFoundError:
        return {"error": "Git command not found. Is Git installed and in your PATH?"}
    except subprocess.CalledProcessError as e:
        # Provide detailed error output from git
        return {"error": f"Git operation failed: {e.stderr}"}

# --- Test Block ---
if __name__ == "__main__":
    # NOTE: Previous tests are commented out to focus on the current task.

    print("\n--- Testing commit_and_push_changes ---")
    
    # 1. Clone the user's repository
    user_repo_url = "https://github.com/love54125/AI_Project.git"
    commit_repo_path = "F:\\Project\\GeminiProject\\commit_test_repo"
    
    # Clean up any previous failed runs
    if os.path.exists(commit_repo_path):
        shutil.rmtree(commit_repo_path, onerror=remove_readonly)
        print("Cleaned up old test directory.")

    print(f"1. Cloning your repository: {user_repo_url}")
    clone_result = clone_repository(user_repo_url, commit_repo_path)
    
    if "error" in clone_result:
        print(f"   - FAILED to clone repository: {clone_result['error']}")
    else:
        print("   - SUCCESS: Repository cloned.")
        
        # 2. Create a new file to commit
        try:
            test_file_path = os.path.join(commit_repo_path, "agent_test_commit.txt")
            with open(test_file_path, "w") as f:
                f.write("This is a test commit from the Gemini Agent.")
            print("2. Created a test file to commit.")

            # 3. Commit and push the changes
            commit_message = "Test commit from Gemini Agent tool"
            target_branch = "main"
            print(f"3. Committing and pushing to '{target_branch}' branch...")
            
            push_result = commit_and_push_changes(commit_repo_path, commit_message, target_branch)
            
            if "error" in push_result:
                print(f"   - FAILED to push changes: {push_result['error']}")
            else:
                print("   - SUCCESS: Commit pushed to remote repository.")
                print("   - Please check your GitHub repository to verify the new commit.")

        except Exception as e:
            print(f"An unexpected error occurred during the test: {e}")
        
        finally:
            # 4. Clean up the local repository
            print("4. Cleaning up local test repository...")
            if os.path.exists(commit_repo_path):
                shutil.rmtree(commit_repo_path, onerror=remove_readonly)
                print("   - SUCCESS: Removed local test repository.")
