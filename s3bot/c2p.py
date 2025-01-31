from atlassian import Confluence
import os

# Set your Confluence credentials and base URL
base_url = "https://confluence.organization.com"
username = "abc123"
password = "$2025"
parent_page_id = '124524340'

# Initialize Confluence instance
confluence = Confluence(
    url=base_url,
    username=username,
    password=password,
    verify_ssl=False
)

def export_page_to_pdf(page_id, output_dir="./confluence-pdf"):
    try:
        # Export current page to PDF
        pdf_export = confluence.export_page(page_id)
        page_info = confluence.get_page_by_id(page_id)
        page_title_raw = page_info['title']
        page_title = page_title_raw.replace("/", "_")
        print(f'Page title is {page_title}')
        file_path = f'{output_dir}/{page_title}.pdf'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        print(f'Filepath is {file_path}')
        with open(file_path, "wb") as pdf_file:
            pdf_file.write(pdf_export)
        print(f'Exported page "{page_title}" to PDF: {file_path}')

        # Recursively export sub-pages
        children = confluence.get_child_pages(page_id)
        for child in children:
            export_page_to_pdf(child['id'], output_dir)
    except Exception as e:
        print(f'Failed to export page ID [{page_id}] to PDF: {str(e)}')

# Get child pages of the parent page
try:
    children = confluence.get_child_pages(parent_page_id)
    if children:
        for child in children:
            export_page_to_pdf(child['id'])
    else:
        print(f'No child pages found for parent page ID {parent_page_id}.')
except Exception as e:
    print(f'Failed to retrieve child pages for parent page ID {parent_page_id}: {str(e)}')

export_page_to_pdf(1223218285)
