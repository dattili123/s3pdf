import os
from atlassian import Jira
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

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

# Directory for storing PDFs (Assumed to exist)
PDF_DIR = "pdf_dir"
PDF_FILE_PATH = os.path.join(PDF_DIR, "jira_issues_detailed.pdf")


def get_jira_issues(project_key, max_results=10):
    """
    Fetches Jira issues from a given project, including the description.
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
            "Created": issue["fields"]["created"],
            "Description": issue["fields"].get("description", "No Description Available")
        }
        issue_list.append(issue_data)
    
    return issue_list


def write_to_pdf(data, pdf_path):
    """
    Writes detailed Jira issue information to a PDF file.
    """
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    y_position = height - 50  # Start position for writing text

    c.setFont("Helvetica-Bold", 14)
    c.drawString(200, y_position, "Jira Issues Detailed Report")
    c.setFont("Helvetica", 10)
    y_position -= 30

    if not data:
        c.drawString(100, y_position, "No issues retrieved from Jira.")
    else:
        for issue in data:
            if y_position < 100:  # Add a new page if content exceeds current page
                c.showPage()
                c.setFont("Helvetica", 10)
                y_position = height - 50

            c.drawString(50, y_position, f'Key: {issue["Key"]}')
            y_position -= 15
            c.drawString(60, y_position, f'Summary: {issue["Summary"]}')
            y_position -= 15
            c.drawString(60, y_position, f'Status: {issue["Status"]}, Reporter: {issue["Reporter"]}, Assignee: {issue["Assignee"]}')
            y_position -= 15
            c.drawString(60, y_position, f'Created: {issue["Created"]}')
            y_position -= 15

            # Add Description (handle multi-line text)
            description_lines = issue["Description"].split('\n')
            c.drawString(60, y_position, "Description:")
            y_position -= 15
            for line in description_lines:
                if y_position < 50:
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    y_position = height - 50
                c.drawString(70, y_position, line.strip())
                y_position -= 15

            y_position -= 20  # Space between issues

    c.save()
    print(f"PDF report with detailed information generated: {pdf_path}")


if __name__ == "__main__":
    jira_issues = get_jira_issues(PROJECT_KEY, max_results=10)
    write_to_pdf(jira_issues, PDF_FILE_PATH)
