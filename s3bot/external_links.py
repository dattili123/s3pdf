import pdfplumber
import os

def extract_hyperlinks_from_pdf(pdf_dir):
    """Extracts URLs from all PDF files in the given directory."""
    urls = set()

    try:
        for file_name in os.listdir(pdf_dir):
            file_path = os.path.join(pdf_dir, file_name)

            if file_name.endswith(".pdf"):  # Process only PDF files
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        for annotation in page.annots or []:
                            uri = annotation.get("uri")
                            if uri:
                                urls.add(uri)

    except Exception as e:
        print(f"Error extracting hyperlinks from {pdf_dir}: {str(e)}")

    return list(urls)

# Call the function with the correct directory path
pdf_directory = "pdf_dir"  # Change this to the actual path if needed
extracted_urls = extract_hyperlinks_from_pdf(pdf_directory)

# Print extracted URLs
print(extracted_urls)
