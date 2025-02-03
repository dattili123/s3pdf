import os
from atlassian import Jira
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

# Jira Configuration
JIRA_URL = "https://your-jira-instance.atlassian.net"
USERNAME = "your-email@example.com"
API_TOKEN = "your-api-token"  # Use API token for authentication
PROJECT_KEY = "PROJECT"  # Replace with your Jira project key

# Directory for storing PDFs (Assumed to exist)
PDF_DIR = "pdf_dir"
PDF_FILE_PATH = os.path.join(PDF_DIR, "jira_issues_improved.pdf")

# Initialize Jira Connection
jira = Jira(
    url=JIRA_URL,
    username=USERNAME,
    password=API_TOKEN,
    cloud=True
)


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


def write_wrapped_text(c, text, x, y, max_width, line_height):
    """
    Writes text with wrapping to fit within a specified width.
    """
    lines = simpleSplit(text, "Helvetica", 10, max_width)
    for line in lines:
        if y < 50:  # Start a new page if space is insufficient
            c.showPage()
            c.setFont("Helvetica", 10)
            y = letter[1] - 50  # Reset y position
        c.drawString(x, y, line)
        y -= line_height
    return y


def write_to_pdf(data, pdf_path):
    """
    Writes detailed Jira issue information to a PDF file with text wrapping.
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

            # Write each field with text wrapping for longer text
            y_position = write_wrapped_text(c, f'Key: {issue["Key"]}', 50, y_position, width - 100, 15)
            y_position = write_wrapped_text(c, f'Summary: {issue["Summary"]}', 60, y_position, width - 100, 15)
            y_position = write_wrapped_text(c, f'Status: {issue["Status"]}, Reporter: {issue["Reporter"]}, Assignee: {issue["Assignee"]}', 60, y_position, width - 100, 15)
            y_position = write_wrapped_text(c, f'Created: {issue["Created"]}', 60, y_position, width - 100, 15)

            # Add Description with text wrapping
            y_position = write_wrapped_text(c, "Description:", 60, y_position, width - 100, 15)
            y_position = write_wrapped_text(c, issue["Description"], 70, y_position, width - 100, 15)

            y_position -= 20  # Space between issues

    c.save()
    print(f"PDF report with improved text wrapping generated: {pdf_path}")


if __name__ == "__main__":
    jira_issues = get_jira_issues(PROJECT_KEY, max_results=10)
    write_to_pdf(jira_issues, PDF_FILE_PATH)
