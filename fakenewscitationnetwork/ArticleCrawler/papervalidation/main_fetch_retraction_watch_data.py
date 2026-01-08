#%% get the retraction_watch file from git
# file location: https://gitlab.com/crossref/retraction-watch-data/-/blob/main/retraction_watch.csv 
import requests, os
#%%


# GitLab project details
PROJECT_ID = "crossref/retraction-watch-data"
FILE_PATH = "retraction_watch.csv"

# GitLab API URLs
RAW_URL = f"https://gitlab.com/{PROJECT_ID}/-/raw/main/{FILE_PATH}"
COMMITS_API_URL = f"https://gitlab.com/api/v4/projects/{PROJECT_ID.replace('/', '%2F')}/repository/commits?path={FILE_PATH}&per_page=1"

# Define local storage paths
DATA_FOLDER = os.path.join(os.path.dirname(__file__), "..", "..", "data")
LOCAL_CSV_PATH = os.path.join(DATA_FOLDER, "retraction_watch.csv")
VERSION_FILE_PATH = os.path.join(DATA_FOLDER, "retraction_watch_version.txt")


def get_file_from_git():
    """
    Fetches the latest version of a file from GitLab and its commit SHA.
    
    Returns:
        tuple: (file_content as bytes, latest_commit_sha as str)
    """
    try:
        # Get the latest commit SHA for the file
        response = requests.get(COMMITS_API_URL)
        response.raise_for_status()
        latest_commit_sha = response.json()[0]["id"]

        # Download the latest version of the file
        file_response = requests.get(RAW_URL)
        file_response.raise_for_status()
        
        return file_response.content, latest_commit_sha

    except requests.exceptions.RequestException as e:
        print(f"Error fetching file from GitLab: {e}")
        return None, None


def save_file(content, version):
    """
    Saves the file content as a CSV and stores the version (commit SHA).
    """
    # Ensure the data directory exists
    os.makedirs(DATA_FOLDER, exist_ok=True)
    
    # Save the CSV file
    with open(LOCAL_CSV_PATH, "wb") as f:
        f.write(content)
    
    # Save the version file
    with open(VERSION_FILE_PATH, "w") as f:
        f.write(version)

    print(f"File saved: {LOCAL_CSV_PATH}")
    print(f"Version saved: {VERSION_FILE_PATH}")
def check_and_update_file():
    """
    Checks if the CSV file and version file exist. If either is missing, download the file.
    If both exist, compare the version and update the file if needed.
    """
    if not os.path.exists(LOCAL_CSV_PATH) or not os.path.exists(VERSION_FILE_PATH):
        # Either the file or version file doesn't exist, so we need to download both
        print("Either the file or version file is missing. Downloading...")
        file_content, latest_sha = get_file_from_git()
        if file_content:
            save_file(file_content, latest_sha)
    else:
        # Both files exist, so check the versions
        with open(VERSION_FILE_PATH, "r") as version_file:
            stored_sha = version_file.read().strip()
        
        file_content, latest_sha = get_file_from_git()

        if file_content and stored_sha != latest_sha:
            print("File is outdated. Downloading the latest version...")
            save_file(file_content, latest_sha)
        else:
            print("File is up-to-date.")

# Call the function
if __name__ == "__main__":
    check_and_update_file()

# %%
