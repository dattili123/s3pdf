import re
import requests
# Function: Export a single Confluence Page to PDF (if missing)
def export_page_to_pdf(page_id, output_dir="pdf_dir"):
    try:
        page_info = confluence.get_page_by_id(page_id)
        
        # Remove special characters and replace spaces with underscores
        page_title = re.sub(r"[^a-zA-Z0-9]", "_", page_info["title"])  
        
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
import requests

import requests

def export_page_and_children(page_id):
    try:
        # Step 1: Always Export the Parent Page
        export_page_to_pdf(page_id)

        # Step 2: Try to Get Child Pages
        try:
            child_pages = list(confluence.get_child_pages(page_id))  
        except requests.exceptions.HTTPError as e:
            print(f"⚠️ HTTPError: Could not retrieve child pages for Page ID {page_id}. Skipping child export... ({e})")
            return  # Skip exporting children, but the parent page remains exported

        # Step 3: Export Child Pages (If They Exist)
        if child_pages:
            print(f"✅ Page ID {page_id} has {len(child_pages)} child pages. Exporting all...")
            for child in child_pages:
                export_page_to_pdf(child["id"])  # Recursively export child pages
        else:
            print(f"✅ Page ID {page_id} has no child pages. Only exporting the parent.")

    except Exception as e:
        print(f"❌ Error processing Page ID {page_id}: {e}")



# Function: Export All Confluence Pages (Handles Parent & Children)
def export_all_confluence_pages():
    for page_id in PAGE_IDS:
        export_page_and_children(page_id)

# Run Confluence PDF Export
export_all_confluence_pages()
