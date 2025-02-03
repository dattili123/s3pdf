from atlassian import Jira
import json

def fetch_jira_details(jira_url, username, password, project_key):
    """
    Fetches Jira details for a given project key and neatly prints the information.

    Args:
        jira_url: The URL of your Jira instance (e.g., "https://your-jira.com").
        username: Your Jira username.
        password: Your Jira password or API token.  Using an API token is highly recommended.
        project_key: The key of the Jira project (e.g., "PROJECTKEY").

    Returns:
        A dictionary containing all fetched Jira issues, or None if an error occurred.
        Prints the details to the console in a readable format.
    """

    try:
        jira = Jira(url=jira_url, username=username, password=password)

        # Search for issues in the specified project.  Adjust JQL as needed.
        # The 'maxResults' parameter can be adjusted if you expect more than 1000 issues.  
        # For very large projects, you might want to implement pagination.
        jql_query = f"project = '{project_key}'"  # Basic JQL query
        issues = jira.search_issues(jql_query, maxResults=False) # maxResults=False gets all issues

        if not issues:
            print(f"No issues found for project key: {project_key}")
            return {}  # Return empty dictionary if no issues

        all_issues_data = {}

        for issue in issues:
            issue_key = issue.key
            issue_data = {
                "summary": issue.fields.summary,
                "status": issue.fields.status.name,
                "created": str(issue.fields.created), # Convert datetime object to string
                "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned",
                "reporter": issue.fields.reporter.displayName if issue.fields.reporter else "Unknown",
                "description": issue.fields.description if hasattr(issue.fields, 'description') else "No Description", # Handle missing description
                # Add other fields as needed (e.g., issue type, priority, custom fields)
                # Example for a custom field (replace 'customfield_10000' with your actual custom field ID):
                # "custom_field_value": issue.fields.customfield_10000 if hasattr(issue.fields, 'customfield_10000') else "N/A",
            }
            all_issues_data[issue_key] = issue_data

            print(f"\n--- Issue: {issue_key} ---")
            for field, value in issue_data.items():
                print(f"{field.capitalize()}: {value}")


        return all_issues_data  # Return the dictionary of issue data

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# Example usage (replace with your Jira credentials and project key):
jira_url = "YOUR_JIRA_URL"  # e.g., "https://yourcompany.atlassian.com"
username = "YOUR_USERNAME"  # or email address if using API token
password_or_token = "YOUR_API_TOKEN_OR_PASSWORD"  # API token is strongly recommended!
project_key = "YOUR_PROJECT_KEY" # e.g., "MYPROJECT"

fetched_data = fetch_jira_details(jira_url, username, password_or_token, project_key)

if fetched_data:
    # You can further process the fetched_data dictionary here if needed.
    # For example, you could save it to a JSON file:
    # with open("jira_data.json", "w", encoding="utf-8") as f:
    #     json.dump(fetched_data, f, indent=4)
    print("\nJira data fetched successfully!")
