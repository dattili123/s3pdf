def export_page_to_pdf(page_id, output_dir=PDF_DIR):
    try:
        page_info = confluence.get_page_by_id(page_id)
        page_title = page_info['title'].replace("/", "_").replace(" ", "_")  # Ensure filename-safe format
        file_path = f"{output_dir}/{page_id}_{page_title}.pdf"

        # Skip if the PDF already exists
        if os.path.exists(file_path):
            print(f"Skipping existing PDF: {file_path}")
            return

        print(f"Fetching page '{page_title}' (ID: {page_id}) from Confluence...")
        pdf_export = confluence.export_page(page_id)

        # Save the PDF
        os.makedirs(output_dir, exist_ok=True)
        with open(file_path, "wb") as pdf_file:
            pdf_file.write(pdf_export)
        print(f"Saved page '{page_title}' (ID: {page_id}) to {file_path}")

    except Exception as e:
        print(f"Failed to export page [{page_id}] to PDF: {str(e)}")

# Function: Export Parent and Child Pages
def export_page_and_children(page_id):
    # Export the parent page first
    export_page_to_pdf(page_id)

    # Get child pages
    child_pages = confluence.get_child_pages(page_id)
    
    if child_pages:
        print(f"Page ID {page_id} has {len(child_pages)} child pages. Exporting all...")
        for child in child_pages:
            export_page_to_pdf(child["id"])  # Recursively export child pages
    else:
        print(f"Page ID {page_id} has no child pages.")

# Function: Export All Confluence Pages (Handles Parent & Children)
def export_all_confluence_pages():
    for page_id in PAGE_IDS:
        export_page_and_children(page_id)

# Run Confluence PDF Export
export_all_confluence_pages()
