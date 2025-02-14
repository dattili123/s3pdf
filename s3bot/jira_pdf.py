from atlassian import Jira
import json
import os
import requests

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image

def write_wrapped_text(c, text, x, y, width, style):
    """Writes text with wrapping using Paragraph and style."""
    p = Paragraph(text, style)
    w, h = p.wrapOn(c, width, 0)  # Wrap the text
    p.drawOn(c, x, y - h)  # Draw the paragraph
    return y - h - style.leading

# Jira Configuration
JIRA_URL = "https://jira.fanniemae.com"
USERNAME = "s5uyav"
API_TOKEN = ""  # Use API token for authentication
PROJECT_KEY = "PANTHER"  # Replace with your Jira project key

PDF_DIR = "pdf_dir"
PDF_FILE_PATH = os.path.join(PDF_DIR, "jira_issues.pdf")
IMAGE_DIR = os.path.join(PDF_DIR, "images")
os.makedirs(IMAGE_DIR, exist_ok=True)

# Initialize Jira Connection
jira = Jira(
    url=JIRA_URL,
    username=USERNAME,
    password=API_TOKEN,
    verify_ssl=False
)

def get_jira_issues(project_key, max_results=500):
    """
    Fetches Jira issues from a given project, including comments and attachments.
    """
    jql_query = f'project = {project_key} and updated >= -2w'
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
            "Assignee": issue["fields"]["assignee"]["displayName"] if issue["fields"].get("assignee") else "Unassigned",
            "Created": issue["fields"]["created"],
            "Description": issue["fields"].get("description", "No description"),
            "Comments": [],
            "Attachments": []
        }
        
        # Fetch comments
        comments_data = jira.issue(issue["key"], fields="comment")["fields"].get("comment", {}).get("comments", [])
        issue_data["Comments"] = [comment["body"] for comment in comments_data]
        
        # Fetch attachments
        if "attachment" in issue["fields"]:
            for attachment in issue["fields"]["attachment"]:
                filename = attachment["filename"]
                if filename.endswith(".png") or filename.endswith(".jpg"):
                    file_path = os.path.join(IMAGE_DIR, filename)
                    response = requests.get(attachment["content"], auth=(USERNAME, API_TOKEN))
                    if response.status_code == 200:
                        with open(file_path, "wb") as f:
                            f.write(response.content)
                        issue_data["Attachments"].append(file_path)
        
        issue_list.append(issue_data)
    
    return issue_list

def write_to_pdf(data, pdf_path):
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = ParagraphStyle(
        name='Normal',
        fontName='Helvetica',
        fontSize=10,
        leading=12,
        wordWrap='CJK',
        alignment=0
    )
    story = []
    index = 1

    if not data:
        story.append(Paragraph("No issues retrieved from Jira.", styles))
    else:
        for issue in data:
            story.append(Paragraph(f'{index}. <b>Key:</b> {issue["Key"]}', styles))
            story.append(Paragraph(f'&nbsp;&nbsp;&nbsp;&nbsp;<b>Summary:</b> {issue["Summary"]}', styles))
            story.append(Paragraph(f'&nbsp;&nbsp;&nbsp;&nbsp;<b>Status:</b> {issue["Status"]}, <b>Reporter:</b> {issue["Reporter"]}, <b>Assignee:</b> {issue["Assignee"]}', styles))
            story.append(Paragraph(f'&nbsp;&nbsp;&nbsp;&nbsp;<b>Created:</b> {issue["Created"]}', styles))
            story.append(Paragraph(f'&nbsp;&nbsp;&nbsp;&nbsp;<b>Description:</b> {issue["Description"]}', styles))
            
            # Add comments
            if issue["Comments"]:
                story.append(Paragraph(f'<b>Comments:</b>', styles))
                for comment in issue["Comments"]:
                    story.append(Paragraph(f'&nbsp;&nbsp;&nbsp;&nbsp;{comment}', styles))
            
            # Add attachments (images)
            if issue["Attachments"]:
                story.append(Paragraph(f'<b>Attachments:</b>', styles))
                for image_path in issue["Attachments"]:
                    story.append(Image(image_path, width=200, height=200))
                    
            story.append(Paragraph("<br/>", styles))
            index += 1

    doc.build(story)

if __name__ == "__main__":
    jira_issues = get_jira_issues(PROJECT_KEY, max_results=500)
    write_to_pdf(jira_issues, PDF_FILE_PATH)
