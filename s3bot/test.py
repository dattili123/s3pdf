import os
import requests

# Constants for authentication and file storage
IMAGE_DIR = "attachments"  # Ensure this directory exists
USERNAME = "your_username"
API_TOKEN = "your_api_token"

def get_multiple_jira_issues(issue_keys):
    """
    Fetches details of multiple Jira issues by their keys, including comments and attachments.
    """
    issue_list = []

    for issue_key in issue_keys:
        issue = jira.issue(issue_key)

        if not issue:
            print(f"No issue found for key: {issue_key}")
            continue  # Skip this issue and move to the next one

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
                if filename.endswith((".png", ".jpg", ".jpeg", ".pdf", ".docx")):  # Adjust as needed
                    file_path = os.path.join(IMAGE_DIR, filename)
                    response = requests.get(attachment["content"], auth=(USERNAME, API_TOKEN), verify=False)

                    if response.status_code == 200:
                        with open(file_path, "wb") as f:
                            f.write(response.content)
                        issue_data["Attachments"].append(file_path)

        issue_list.append(issue_data)

    return issue_list


issue_keys = [""]  # Your list of issue keys
issues_data = get_multiple_jira_issues(issue_keys)

for issue in issues_data:
    print(issue)
