import os
import requests

# Constants for authentication and file storage
IMAGE_DIR = "attachments"  # Ensure this directory exists
USERNAME = "your_username"
API_TOKEN = "your_api_token"

def get_specific_jira_issue(issue_key):
    """
    Fetches details of a specific Jira issue by its key, including comments and attachments.
    """
    issue = jira.issue(issue_key)

    if not issue:
        print(f"No issue found for key: {issue_key}")
        return None

    issue_data = {
        "Key": issue["key"],
        "Summary": issue["fields"]["summary"],
        "Status": issue["fields"]["status"]["name"],
        "Reporter": issue["fields"]["reporter"]["displayName"],
        "Assignee": issue["fields"].get("assignee", {}).get("displayName", "Unassigned"),
        "Created": issue["fields"]["created"],
        "Description": issue["fields"].get("description", "No description"),
        "Comments": [],
        "Attachments": []
    }

    # Fetch comments
    comments_data = issue["fields"].get("comment", {}).get("comments", [])
    issue_data["Comments"] = [comment["body"] for comment in comments_data]

    # Fetch attachments
    if "attachment" in issue["fields"]:
        for attachment in issue["fields"]["attachment"]:
            filename = attachment["filename"]
            if filename.endswith(".png") or filename.endswith(".jpg") or filename.endswith(".jpeg"):  # Adjust as needed
                file_path = os.path.join(IMAGE_DIR, filename)
                response = requests.get(attachment["content"], auth=(USERNAME, API_TOKEN), verify=False)
                
                if response.status_code == 200:
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    issue_data["Attachments"].append(file_path)

    return issue_data



issue_keys = []

issues_data = get_specific_jira_issues(issue_keys)
for issue in issues_data:
    print(issue)
