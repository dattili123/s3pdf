from jira import JIRA
import requests
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

# Jira Credentials
JIRA_SERVER = "https://your-jira-instance.atlassian.net"
JIRA_USER = "your-email@example.com"
JIRA_API_TOKEN = "your-api-token"

# Establish Jira Connection
jira = JIRA(server=JIRA_SERVER, basic_auth=(JIRA_USER, JIRA_API_TOKEN))

def fetch_jira_issues_to_pdf(output_pdf):
    """
    Fetch Jira issues based on a JQL query, retrieve details, comments, and image attachments, 
    and save them into a PDF.

    :param output_pdf: Output PDF file path
    """
    # JQL Query (taken from your image)
    jql_query = '''
    project in ("MTS Panther Service Desk") 
    AND component in (SFA) 
    AND assignee in (s5uyav) 
    AND priority in (Highest, Critical, Blocker) 
    AND createdDate >= startOfMonth(-7) 
    AND createdDate <= startOfMonth(-2) 
    ORDER BY created DESC, status
    '''

    # Fetch Jira issues using JQL
    issues = jira.search_issues(jql_query, maxResults=50)  # Adjust maxResults if needed

    if not issues:
        print("No Jira issues found for the given query.")
        return

    # Create PDF
    pdf_buffer = io.BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter
    y_position = height - 40  # Start position for text

    for issue in issues:
        # Fetch issue details
        issue_key = issue.key
        issue_summary = issue.fields.summary
        issue_description = issue.fields.description or "No description available"
        issue_comments = jira.comments(issue)
        attachments = issue.fields.attachment

        # Write issue details to PDF
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(30, y_position, f"Issue: {issue_key} - {issue_summary}")
        y_position -= 20

        pdf.setFont("Helvetica", 12)
        pdf.drawString(30, y_position, "Description:")
        y_position -= 15
        pdf.setFont("Helvetica", 10)
        for line in issue_description.split("\n"):
            pdf.drawString(30, y_position, line)
            y_position -= 15

        # Adding Comments
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(30, y_position - 10, "Comments:")
        y_position -= 25

        pdf.setFont("Helvetica", 10)
        for comment in issue_comments:
            comment_author = comment.author.displayName
            comment_body = comment.body
            pdf.drawString(30, y_position, f"{comment_author}:")
            y_position -= 15
            for line in comment_body.split("\n"):
                pdf.drawString(30, y_position, line)
                y_position -= 15
            y_position -= 10  # Add spacing

        # Adding Attachments (Images Only)
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(30, y_position - 10, "Attachments:")
        y_position -= 25

        for attachment in attachments:
            if attachment.mimeType.startswith("image"):  # Check if it's an image
                image_response = requests.get(attachment.content, auth=(JIRA_USER, JIRA_API_TOKEN))
                if image_response.status_code == 200:
                    image = Image.open(io.BytesIO(image_response.content))
                    image.thumbnail((500, 300))  # Resize to fit PDF
                    image_reader = ImageReader(image)

                    if y_position < 100:  # Add a new page if space is insufficient
                        pdf.showPage()
                        y_position = height - 40

                    pdf.drawImage(image_reader, 30, y_position - 150, width=200, height=100)  # Insert image
                    y_position -= 160

        # Add spacing between issues
        y_position -= 30
        pdf.showPage()  # Start a new page for the next issue

    # Save PDF
    pdf.save()
    with open(output_pdf, "wb") as f:
        f.write(pdf_buffer.getvalue())

    print(f"PDF saved as {output_pdf}")

# Example Usage
fetch_jira_issues_to_pdf("filtered_jira_issues.pdf")
