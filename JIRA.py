from atlassian import Jira
import json

# ... (Your Jira configuration and connection setup)

def get_all_jira_issues(project_key, page_size=500):  # Adjust page size as needed
    """Retrieves all Jira issues using pagination."""

    jql_query = f'project = "{project_key}" ORDER BY created DESC'
    all_issues = []
    start_at = 0  # Start from the first issue

    while True:
        try:
            issues = jira.search_issues(jql_query, startAt=start_at, maxResults=page_size)

            if not issues: # No more issues
                break

            for issue in issues:
                issue_data = {  # Extract issue data (as in your working code)
                    "Key": issue.key,
                    "Summary": issue.fields.summary,
                    "Status": issue.fields.status.name,
                    "Reporter": issue.fields.reporter.displayName if issue.fields.reporter else "Unknown",
                    "Assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned",
                    "Created": str(issue.fields.created),
                    "Description": issue.fields.description if hasattr(issue.fields, 'description') else "No Description"
                }
                all_issues.append(issue_data)

            start_at += page_size  # Move to the next page

        except Exception as e:  # Handle potential errors during requests
            print(f"Error during Jira request: {e}")
            break  # Or implement retry logic if needed

    return all_issues

if __name__ == "__main__":
    all_issues = get_all_jira_issues(PROJECT_KEY)
    if all_issues:
        print(json.dumps(all_issues, indent=4))
    else:
        print("No issues retrieved from Jira.")
