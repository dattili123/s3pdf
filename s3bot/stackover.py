import requests
import io
import pdfplumber
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

# Constants (Replace with actual values)
API_BASE_URL = "https://fnma.stackenterprise.co/api/2.3"
API_KEY = "rikfbjrkskhbejwiejndj"

# Fetch questions and answers
def fetch_questions():
    url = f"{API_BASE_URL}/questions?order=desc&sort=activity&site=stackoverflow&key={API_KEY}"
    response = requests.get(url)
    return response.json().get("items", [])

def fetch_answers(question_id):
    url = f"{API_BASE_URL}/questions/{question_id}/answers?order=desc&sort=activity&site=stackoverflow&key={API_KEY}"
    response = requests.get(url)
    return response.json().get("items", [])

# Fetch images embedded in posts
def extract_images(post_body):
    images = []
    if "<img " in post_body:
        parts = post_body.split('<img ')
        for part in parts[1:]:
            src_start = part.find('src="') + 5
            src_end = part.find('"', src_start)
            img_url = part[src_start:src_end]
            if img_url.startswith("http"):
                images.append(img_url)
    return images

# Generate PDF
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
            c.drawString(60, y_position, f"A: {answer.get('body', 'No answer text')[:100]}...")
            y_position -= 20
            
            # Extract images and add to PDF
            images = extract_images(answer.get('body', ''))
            for img_url in images:
                try:
                    img_response = requests.get(img_url, stream=True)
                    img = Image.open(img_response.raw)
                    img.thumbnail((200, 200))
                    img_io = io.BytesIO()
                    img.save(img_io, format="PNG")
                    img_io.seek(0)
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
