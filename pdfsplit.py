from PyPDF2 import PdfReader, PdfWriter
import os

def split_pdf_by_size(input_pdf_path, output_dir, size_limit_mb=1):
    """
    Splits a PDF file into smaller PDFs, each approximately size_limit_mb in size.

    Args:
        input_pdf_path (str): Path to the input PDF file.
        output_dir (str): Directory where split PDFs will be saved.
        size_limit_mb (int): Maximum size of each split PDF in megabytes.
    """
    os.makedirs(output_dir, exist_ok=True)
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()
    current_size = 0
    part_number = 1

    for i, page in enumerate(reader.pages):
        writer.add_page(page)
        
        # Add the estimated size of the current page
        page_size = len(page.extract_text().encode("utf-8")) / (1024 * 1024)  # Size in MB
        current_size += page_size

        # If the current size exceeds the limit or it's the last page, save the file
        if current_size >= size_limit_mb or i == len(reader.pages) - 1:
            output_path = os.path.join(output_dir, f"part_{part_number}.pdf")
            with open(output_path, "wb") as output_file:
                writer.write(output_file)
            print(f"Saved: {output_path} (Size: {current_size:.2f} MB)")
            writer = PdfWriter()  # Reset the writer for the next part
            current_size = 0
            part_number += 1

    print(f"PDF split into {part_number - 1} parts and saved in {output_dir}.")
