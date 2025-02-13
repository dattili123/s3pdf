import os
from PyPDF2 import PdfReader, PdfWriter

def split_pdf(input_pdf, output_folder, pages_per_split=10):
    """
    Splits a large PDF into multiple smaller PDFs.
    
    :param input_pdf: Path to the input PDF file.
    :param output_folder: Folder to save the split PDFs.
    :param pages_per_split: Number of pages per split file.
    """
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Read the input PDF
    pdf_reader = PdfReader(input_pdf)
    total_pages = len(pdf_reader.pages)

    # Split logic
    for i in range(0, total_pages, pages_per_split):
        pdf_writer = PdfWriter()
        for j in range(i, min(i + pages_per_split, total_pages)):
            pdf_writer.add_page(pdf_reader.pages[j])

        output_filename = os.path.join(output_folder, f"split_{i+1}-{min(i + pages_per_split, total_pages)}.pdf")
        with open(output_filename, "wb") as output_pdf:
            pdf_writer.write(output_pdf)
        
        print(f"Created: {output_filename}")

# Example Usage
input_pdf = "large_document.pdf"  # Path to the large PDF file
output_folder = "split_pdfs"      # Folder to store the split PDFs
split_pdf(input_pdf, output_folder, pages_per_split=10)  # Change pages_per_split as needed
