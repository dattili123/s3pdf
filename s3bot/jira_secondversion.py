import requests
import json
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image
from reportlab.lib.enums import TA_JUSTIFY
import os
from urllib.parse import quote_plus  # Import for URL encoding


# Jira Configuration
JIRA_URL = "https://jira..com"
USERNAME = ""
API_TOKEN = "rivonix$2025"

# PDF Output
PDF_DIR = "pdf_dir"
os.makedirs(PDF_DIR, exist_ok=True)
PDF_FILE_PATH = os.path.join(PDF_DIR, "jira_issues.pdf")

def get_jira_issues(jql_query, max_results=1000):
    """Fetches Jira issues directly via the REST API."""

    # 1. Construct the API endpoint URL.  Crucially, URL-encode the JQL query.
    base_url = f"{JIRA_URL}/rest/api/2/search"
    encoded_jql = quote_plus(jql_query)  # Properly URL-encode the JQL
    fields = "comment,attachment,summary,status,reporter,assignee,created,description,priority,components" #Comma separated is more reliable
    url = f"{base_url}?jql={encoded_jql}&maxResults={max_results}&fields={fields}"

    # 2. Make the API request with proper authentication.
    headers = {
        "Content-Type": "application/json",  # Important: Set the content type
    }
    auth = (USERNAME, API_TOKEN)

    try:
        response = requests.get(url, headers=headers, auth=auth, verify=False)  # Corrected auth
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        response_json = response.json() #Get the JSON

    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")
        print(f"  URL: {url}")  # Print the *full* URL for debugging
        if hasattr(e, 'response') and e.response:
            print(f"  Response Status Code: {e.response.status_code}")
            print(f"  Response Content:\n{e.response.text}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        print(f"  Response Content:\n{response.text}")  # Print raw response for debugging
        return []


    if "issues" not in response_json:
        print("No issues found in response.")
        return []

    issue_list = []
    for issue in response_json["issues"]:
        fields = issue.get('fields', {})  # Handle missing 'fields' key

        # Use .get() with defaults for robust field handling
        issue_data = {
            "Key": issue.get("key", "No Key"),
            "Summary": fields.get("summary", "No Summary"),
            "Status": fields.get("status", {}).get("name", "No Status"),
            "Reporter": fields.get("reporter", {}).get("displayName", "No Reporter"),
            "Assignee": fields.get("assignee", {}).get("displayName", "Unassigned"),
            "Created": fields.get("created", "No Creation Date"),
            "Description": fields.get("description", "No Description"),
            "Priority": fields.get("priority", {}).get("name", "N/A"),
            "Components": ", ".join([comp.get("name", "Unknown Component") for comp in fields.get("components", [])]),
            "Comments": [],
            "Attachments": [],
        }

        # Comments
        for comment in fields.get("comment", {}).get("comments", []):
            issue_data["Comments"].append({
                'author': comment.get("author", {}).get("displayName", "Unknown Author"),
                'body': comment.get("body", "No Comment Body"),
                'created': comment.get("created", "Unknown Date"),
            })

        # Attachments
        for attachment in fields.get("attachment", []):
            issue_data["Attachments"].append({
                'filename': attachment.get("filename", "Unknown Filename"),
                'content_url': attachment.get("content", ""),
                'author': attachment.get("author", {}).get("displayName", "Unknown Author"),
                'created': attachment.get("created", "Unknown Date"),
            })

        issue_list.append(issue_data)

    return issue_list



def write_to_pdf(data, pdf_path):
    """Generates PDF, handling missing data gracefully."""
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = ParagraphStyle(name='Normal', fontName="Helvetica", fontSize=10, leading=12, alignment=TA_JUSTIFY)
    comment_style = ParagraphStyle(name='Comment', parent=styles, fontSize=9, leading=11, leftIndent=20)
    attachment_style = ParagraphStyle(name='Attachment', parent=styles, fontSize=9, leading=11, textColor='blue', leftIndent=20)

    story = []
    index = 1

    if not data:
        story.append(Paragraph("No issues retrieved from Jira.", styles))
        doc.build(story)  # Build even if empty
        return

    for issue in data:
        story.append(Paragraph(f"{index}. <b>Key:</b> {issue['Key']}  <b>Priority:</b> {issue['Priority']} <b>Component:</b> {issue['Components']}", styles))
        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp; <b>Summary:</b> {issue['Summary']}", styles))
        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Status:</b> {issue['Status']} <b>Reporter:</b> {issue['Reporter']}, <b>Assignee:</b> {issue['Assignee']}", styles))
        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Created:</b> {issue['Created']}", styles))
        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp; <b>Description:</b> {issue['Description']}", styles))

        if issue["Comments"]:
            story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;<b>Comments:</b>", styles))
            for comment in issue["Comments"]:
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp; - <i>{comment['author']} ({comment['created']}):</i> {comment['body']}", comment_style))

        if issue["Attachments"]:
            story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;<b>Attachments:</b>", styles))
            for attachment in issue["Attachments"]:
                if attachment['filename'].lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) and attachment['content_url']:
                    try:
                        response = requests.get(attachment['content_url'], auth=(USERNAME, API_TOKEN), verify=False)  # Corrected auth
                        response.raise_for_status()

                        image_path = os.path.join(PDF_DIR, attachment['filename'])
                        with open(image_path, 'wb') as f:
                            f.write(response.content)

                        img = Image(image_path, width=200, height=150)
                        img.hAlign = 'LEFT'
                        story.append(img)
                        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp; - Attachment: {attachment['filename']} (Uploaded by: {attachment['author']} on {attachment['created']})", attachment_style))

                    except requests.exceptions.RequestException as e:
                        print(f"Error downloading attachment {attachment['filename']}: {e}")
                        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp; - Could not download: {attachment['filename']}", comment_style))
                    except Exception as e:
                        print(f"Other error with Attachment {attachment['filename']}: {e}")
                        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp; - Could not process: {attachment['filename']}", comment_style))
                elif attachment['content_url']: #Show name if it's not an image
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp; - Attachment: {attachment['filename']} (Uploaded by: {attachment['author']} on {attachment['created']})", attachment_style))
                else:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp; - Attachment(No URL): {attachment.get('filename', 'Unknown Filename')}", comment_style))
        story.append(Paragraph('&nbsp;', styles))
        story.append(Paragraph("<br/>", styles))
        index += 1

    doc.build(story)



if __name__ == "__main__":
    jql_query = """
        project in ("MTS Panther Service Desk")
        AND component in (SFA)
        AND assignee in (s5uyav)
        AND priority in (Highest, Critical, Blocker)
        AND createdDate >= startOfMonth(-7)
        AND createdDate <= startOfMonth(-2)
        ORDER BY created DESC, status
        """
    jira_issues = get_jira_issues(jql_query, max_results=10)  # Keep max_results small for testing
    if jira_issues:
        write_to_pdf(jira_issues, PDF_FILE_PATH)
        print(f"PDF report generated at: {PDF_FILE_PATH}")
