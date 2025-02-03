from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph

def write_wrapped_text(c, text, x, y, width, style):
    """Writes text with wrapping using Paragraph and style."""
    p = Paragraph(text, style)
    w, h = p.wrapOn(c, width, 0)  # Wrap the text
    p.drawOn(c, x, y - h)  # Draw the paragraph
    return y - h - style.leading  # Return the updated y position

def write_to_pdf(data, pdf_path):
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = ParagraphStyle(
        name='Normal',
        fontName='Helvetica',
        fontSize=10,
        leading=12,  # Adjust leading for spacing between lines
        wordWrap='CJK', # or other appropriate word wrapping
        alignment=0 # alignment 0: left, 1: center, 2: right, 3: justify
    )
    story = []

    if not data:
        story.append(Paragraph("No issues retrieved from Jira.", styles))
    else:
        for issue in data:
            story.append(Paragraph(f'<b>Key:</b> {issue["Key"]}', styles))
            story.append(Paragraph(f'<b>Summary:</b> {issue["summary"]}', styles))
            story.append(Paragraph(f'<b>Status:</b> {issue["status"]}, <b>Reporter:</b> {issue["Reporter"]}, <b>Assignee:</b> {issue["Assignee"]}', styles))
            story.append(Paragraph(f'<b>Created:</b> {issue["Created"]}', styles))
            story.append(Paragraph("<br/>", styles))  # Add some vertical space

    doc.build(story)

# Example usage (replace with your actual data and path)
data = [
    {"Key": "PROJECT-123", "summary": "This is a very long summary that might span multiple lines and cause issues with the previous code.", "status": "In Progress", "Reporter": "John Doe", "Assignee": "Jane Smith", "Created": "2024-07-26"},
    {"Key": "PROJECT-456", "summary": "Short summary.", "status": "Done", "Reporter": "Alice Johnson", "Assignee": "Bob Williams", "Created": "2024-07-25"},
    # ... more data
]
write_to_pdf(data, "jira_report.pdf")
