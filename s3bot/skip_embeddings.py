import json
import os

PROCESSED_PDFS_FILE = "./processed_pdfs.json"

def load_processed_pdfs():
    """Load the list of processed PDFs from a JSON file."""
    if os.path.exists(PROCESSED_PDFS_FILE):
        with open(PROCESSED_PDFS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_processed_pdfs(processed_pdfs):
    """Save the list of processed PDFs to a JSON file."""
    with open(PROCESSED_PDFS_FILE, "w") as f:
        json.dump(processed_pdfs, f)

def store_all_pdfs_in_chromadb(pdf_dir: str, embedding_function):
    """Store embeddings for new PDFs only, skipping already processed ones."""
    if not isinstance(pdf_dir, str):
        raise TypeError(f"Expected pdf_dir to be a string, got {type(pdf_dir)} instead.")

    # Load the list of already processed PDFs
    processed_pdfs = load_processed_pdfs()
    
    for pdf_file in os.listdir(pdf_dir):
        if pdf_file.endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, pdf_file)

            # Check if the file has already been processed
            if pdf_file in processed_pdfs:
                print(f"Skipping already processed PDF: {pdf_file}")
                continue  # Skip processing

            print(f"Processing new PDF: {pdf_file}")
            try:
                process_large_pdf(pdf_path, batch_size=10)
                processed_pdfs[pdf_file] = True  # Mark as processed
                save_processed_pdfs(processed_pdfs)  # Save updated processed list
            except Exception as e:
                print(f"Error processing PDF {pdf_file}: {str(e)}")

    return collection
