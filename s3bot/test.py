def get_specific_jira_issues(issue_keys):
    """
    Fetches details for a list of specific Jira issues.
    """
    issue_list = []
    
    for issue_key in issue_keys:
        try:
            issue = jira.issue(issue_key)
            issue_data = {
                "Key": issue["key"],
                "Summary": issue["fields"]["summary"],
                "Status": issue["fields"]["status"]["name"],
                "Reporter": issue["fields"]["reporter"]["displayName"],
                "Assignee": issue["fields"].get("assignee", {}).get("displayName", "Unassigned"),
                "Created": issue["fields"]["created"],
                "Description": issue["fields"].get("description", "No description"),
                "Comments": [comment["body"] for comment in issue["fields"].get("comment", {}).get("comments", [])]
            }
            issue_list.append(issue_data)
        except Exception as e:
            print(f"Error retrieving {issue_key}: {e}")

    return issue_list


issue_keys = []

issues_data = get_specific_jira_issues(issue_keys)
for issue in issues_data:
    print(issue)
