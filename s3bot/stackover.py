import os
import requests
import io
import pdfplumber
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
from bs4 import BeautifulSoup
import html

# Constants
API_BASE_URL = "https://fnma.stackenterprise.co/api/2.3"
API_KEY = os.getenv("STACKOVERFLOW_API_KEY")  # Store API key securely

HEADERS = {
    "Accept": "application/json"
}

# Fetch questions from Stack Overflow Enterprise
def fetch_questions():
    url = f"{API_BASE_URL}/questions?order=desc&sort=activity&site=fnma&key={API_KEY}"
    response = requests.get(url, headers=HEADERS)
    return response.json().get("items", [])

# Fetch answers for a question
def fetch_answers(question_id):
    url = f"{API_BASE_URL}/questions/{question_id}/answers?order=desc&sort=activity&site=fnma&key={API_KEY}&filter=withbody"
    response = requests.get(url, headers=HEADERS)
    return response.json().get("items", [])

# Extract text from HTML
def clean_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator=" ")

# Extract image URLs from HTML content
def extract_images(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    images = [img["src"] for img in soup.find_all("img") if img.get("src", "").startswith("http")]
    return images

# Generate PDF with questions, answers, and images
def generate_pdf(questions):
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter
    y_position = height - 50

    for question in questions:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y_position, f"Q: {question['title']}")
        y_position -= 20

        # Fetch answers
        answers = fetch_answers(question['question_id'])
        for answer in answers:
            c.setFont("Helvetica", 10)
            answer_text = clean_html(answer.get("body", "No answer text"))
            c.drawString(60, y_position, f"A: {answer_text[:150]}...")
            y_position -= 20
            
            # Extract images and add to PDF
            images = extract_images(answer.get("body", ""))
            for img_url in images:
                try:
                    img_response = requests.get(img_url, stream=True)
                    img = Image.open(img_response.raw)
                    img.thumbnail((150, 150))
                    img_io = io.BytesIO()
                    img.save(img_io, format="PNG")
                    img_io.seek(0)

                    if y_position - 150 < 50:
                        c.showPage()
                        y_position = height - 50

                    c.drawImage(ImageReader(img_io), 60, y_position - 150, width=100, height=100)
                    y_position -= 120
                except Exception as e:
                    print(f"Error loading image: {e}")
            
            y_position -= 20
        
        y_position -= 20

        if y_position < 50:
            c.showPage()
            y_position = height - 50

    c.save()
    pdf_buffer.seek(0)
    with open("stackoverflow_data.pdf", "wb") as f:
        f.write(pdf_buffer.getvalue())

# Main Execution
if __name__ == "__main__":
    questions = fetch_questions()
    generate_pdf(questions)
    print("PDF generated successfully: stackoverflow_data.pdf")
