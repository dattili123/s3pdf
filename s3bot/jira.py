rom atlassian import Jira
import json
# Jira Configuration
JIRA_URL = "https://your-jira-instance.atlassian.net"
USERNAME = "your-email@example.com"
API_TOKEN = "your-api-token"  # Use API token for authentication
PROJECT_KEY = "PROJECT"  # Replace with your Jira project key
# Initialize Jira Connection
jira = Jira(
    url=JIRA_URL,
    username=USERNAME,
    password=API_TOKEN,
    cloud=True
)
def get_jira_issues(project_key, max_results=10):
    """
    Fetches Jira issues from a given project.
    :param project_key: Jira project key.
    :param max_results: Number of issues to retrieve.
    :return: List of issue details.
    """
    jql_query = f'project = {project_key} ORDER BY created DESC'
    issues = jira.jql(jql_query, limit=max_results)
    
    if "issues" not in issues:
        print("No issues found or invalid response.")
        return []
    
    issue_list = []
    for issue in issues["issues"]:
        issue_data = {
            "Key": issue["key"],
            "Summary": issue["fields"]["summary"],
            "Status": issue["fields"]["status"]["name"],
            "Reporter": issue["fields"]["reporter"]["displayName"],
            "Assignee": issue["fields"]["assignee"]["displayName"] if issue["fields"]["assignee"] else "Unassigned",
            "Created": issue["fields"]["created"]
        }
        issue_list.append(issue_data)
    
    return issue_list
if __name__ == "__main__":
    jira_issues = get_jira_issues(PROJECT_KEY, max_results=5)
    if jira_issues:
        print(json.dumps(jira_issues, indent=4))
    else:
        print("No issues retrieved from Jira.")
