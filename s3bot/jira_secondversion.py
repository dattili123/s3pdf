from atlassian import Jira
import json
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image
from reportlab.lib.enums import TA_JUSTIFY  # Import for clearer alignment
import os
import requests  # Import the requests library


# Jira Configuration
JIRA_URL = "https://jira.fanniemae.com"  # Replace with your Jira URL
USERNAME = "gbudfa"
API_TOKEN = "rivonix$2025"  # Use API token for authentication
# NO LONGER NEEDED: PROJECT_KEY = "PANTHER"  # Replace with your Jira project key

# PDF Output
PDF_DIR = "pdf_dir"
os.makedirs(PDF_DIR, exist_ok=True)  # Ensure the output directory exists
PDF_FILE_PATH = os.path.join(PDF_DIR, "jira_issues.pdf")

# --- Initialize Jira Connection ---
jira = Jira(
    url=JIRA_URL,
    username=USERNAME,
    password=API_TOKEN,
    verify_ssl=False  # Consider setting up proper SSL verification in production
)


def get_jira_issues(jql_query, max_results=1000):
    """
    Fetches Jira issues from a given project using a JQL query, including comments and attachments.

    :param jql_query: The JQL query string.
    :param max_results: Number of issues to retrieve.
    :return: List of issue details.
    """
    issues = jira.jql(jql_query, limit=max_results, fields=['comment', 'attachment', 'summary', 'status', 'reporter', 'assignee', 'created', 'description', 'priority', 'components']) #Added fields to query

    if "issues" not in issues:
        print("No issues found or invalid response.")
        return []

    issue_list = []
    for issue in issues["issues"]:
        # --- Extract Basic Issue Data ---
        issue_data = {
            "Key": issue["key"],
            "Summary": issue["fields"]["summary"],
            "Status": issue["fields"]["status"]["name"],
            "Reporter": issue["fields"]["reporter"]["displayName"],
            "Assignee": issue["fields"]["assignee"]["displayName"] if issue["fields"]["assignee"] else "Unassigned",
            "Created": issue["fields"]["created"],
            "Description": issue["fields"]["description"],
            "Priority": issue["fields"]["priority"]["name"] if issue["fields"]["priority"] else "N/A", #Get priority.  Handle if it's None
            "Components": ", ".join([comp["name"] for comp in issue["fields"]["components"]]) if issue["fields"]["components"] else "No Component",  #Handle components

            "Comments": [],  # Initialize an empty list for comments
            "Attachments": []  # Initialize an empty list for attachments
        }

        # --- Extract Comments ---
        if 'comment' in issue['fields'] and issue['fields']['comment']['comments']:
            for comment in issue['fields']['comment']['comments']:
                comment_data = {
                    'author': comment['author']['displayName'],
                    'body': comment['body'],
                    'created': comment['created']
                }
                issue_data["Comments"].append(comment_data)

        # --- Extract Attachments ---
        if 'attachment' in issue['fields'] and issue['fields']['attachment']:
            for attachment in issue['fields']['attachment']:
                attachment_data = {
                    'filename': attachment['filename'],
                    'content_url': attachment['content'],  # URL to download the attachment
                    'author' : attachment['author']['displayName'],
                    'created' : attachment['created'],
                }
                issue_data["Attachments"].append(attachment_data)
        # print(json.dumps(issue_data, indent=4)) # Uncomment for debugging
        issue_list.append(issue_data)

    return issue_list



def write_to_pdf(data, pdf_path):
    """
    Generates a PDF report from the provided Jira issue data, including comments and image attachments.

    :param data: List of Jira issue dictionaries.
    :param pdf_path: Path to save the generated PDF.
    """
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = ParagraphStyle(
        name='Normal',
        fontName="Helvetica",
        fontSize=10,
        leading=12,
        alignment=TA_JUSTIFY  # Use TA_JUSTIFY for justified text
    )
    
    #Style for comments
    comment_style = ParagraphStyle(
        name='Comment',
        parent=styles,
        fontSize=9,
        leading=11,
        leftIndent=20  # Indent comments
    )
        #Style for attachment names
    attachment_style = ParagraphStyle(
        name='Attachment',
        parent=styles,
        fontSize=9,
        leading=11,
        textColor='blue', #Make them blue so they look like links.
        leftIndent=20  # Indent attachment
    )

    story = []
    index = 1

    if not data:
        story.append(Paragraph("No issues retrieved from Jira.", styles))
    else:
        for issue in data:
            story.append(Paragraph(f"{index}. <b>Key:</b> {issue['Key']}  <b>Priority:</b> {issue['Priority']} <b>Component:</b> {issue['Components']}", styles))  # Include priority and component
            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp; <b>Summary:</b> {issue['Summary']}", styles))
            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Status:</b> {issue['Status']} <b>Reporter:</b> {issue['Reporter']}, <b>Assignee:</b> {issue['Assignee']}", styles))
            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Created:</b> {issue['Created']}", styles))
            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp; <b>Description:</b> {issue['Description']}", styles))

            # --- Add Comments ---
            if issue["Comments"]:
                story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;<b>Comments:</b>", styles))
                for comment in issue["Comments"]:
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp; - <i>{comment['author']} ({comment['created']}):</i> {comment['body']}", comment_style))

            # --- Add Attachments ---
            if issue["Attachments"]:
                story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;<b>Attachments:</b>", styles))
                for attachment in issue["Attachments"]:
                    # Download and embed images directly
                    if attachment['filename'].lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        try:
                            # print(f"Attempting to get: {attachment['content_url']}")   #Debugging print
                            response = requests.get(attachment['content_url'], auth=(USERNAME, API_TOKEN), verify=False) # Added verify
                            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

                            image_path = os.path.join(PDF_DIR, attachment['filename'])
                            with open(image_path, 'wb') as f:
                                f.write(response.content)
                            
                            #Add the image.
                            img = Image(image_path, width=200, height=150)  # Adjust width and height as needed
                            img.hAlign = 'LEFT' #Align left.
                            story.append(img)

                            #Add a caption
                            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp; - Attachment: {attachment['filename']} (Uploaded by: {attachment['author']} on {attachment['created']})", attachment_style))

                        except requests.exceptions.RequestException as e:
                            print(f"Error downloading attachment {attachment['filename']}: {e}")
                            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp; - Could not download attachment: {attachment['filename']}", comment_style))
                        except Exception as e: #Catch other exceptions
                            print(f"Error processing attachment {attachment['filename']}: {e}")
                            story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp; - Could not process attachment: {attachment['filename']}", comment_style))


                    else: #If it's not an image, just show the filename
                        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp; - Attachment: {attachment['filename']} (Uploaded by: {attachment['author']} on {attachment['created']})", attachment_style))


            story.append(Paragraph('&nbsp;', styles))  # Add some vertical space
            story.append(Paragraph("<br/>", styles))  # Add some vertical space
            index += 1

    doc.build(story)



if __name__ == "__main__":
    jql_query = '''
        project in ("MTS Panther Service Desk") 
        AND component in (SFA) 
        AND assignee in (s5uyav) 
        AND priority in (Highest, Critical, Blocker) 
        AND createdDate >= startOfMonth(-7) 
        AND createdDate <= startOfMonth(-2) 
        ORDER BY created DESC, status
        '''
    jira_issues = get_jira_issues(jql_query, max_results=500)
    write_to_pdf(jira_issues, PDF_FILE_PATH)
    print(f"PDF report generated at: {PDF_FILE_PATH}")
