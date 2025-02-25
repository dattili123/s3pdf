import re
from PyPDF2 import PdfReader

JIRA_BASE_URL = "https://8443/browse/"  # Update this with your Jira base URL
JIRA_ISSUES_PDF_PATH = "./pdf_dir/jira_issues.pdf"  # Path to the Jira issues PDF

def extract_jira_keys_from_pdf(pdf_path, relevant_pages):
    """
    Extract Jira issue keys only from the specified relevant pages of a PDF.
    """
    jira_keys = set()

    try:
        pdf_reader = PdfReader(pdf_path)
        for page_num in relevant_pages:  # Only process relevant pages
            if 0 <= page_num < len(pdf_reader.pages):
                text = pdf_reader.pages[page_num].extract_text()
                if text:
                    found_issues = re.findall(r'\b[A-Z]+-\d+\b', text)  # Matches Jira issue format (e.g., PANTHER-2462)
                    jira_keys.update(found_issues)

    except Exception as e:
        print(f"Error reading Jira issues PDF: {str(e)}")
    
    return list(jira_keys)

def query_chromadb_and_generate_response(user_query, embedding_function, collection, model_id, region="us-east-1"):
    query_embedding = embedding_function([user_query])[0]
    results = collection.query(query_embedding, n_results=5)

    if not results or "documents" not in results or not results["documents"]:
        return "No relevant data found in the database.", [], [], []

    # Retrieve relevant text chunks and metadata
    documents = [doc for sublist in results["documents"] for doc in sublist]
    metadata = results.get("metadatas", [])
    print(f"Metadata is as follows: {metadata}")

    confluence_links = []
    jira_links = []
    other_pdf_sources = set()
    relevant_jira_pages = set()  # Stores the relevant pages in jira_issues.pdf

    for meta in metadata[0]:
        if isinstance(meta, dict):
            source = meta.get("source", "Unknown Source")
            page = meta.get("page", "Unknown Page")
            print(f"Processing metadata: source=({source}), page=({page})")

            # Extract Confluence page IDs from filename
            match = re.match(r".*/(\d+)_.*\.pdf", source)
            if match:
                page_id = match.group(1)
                confluence_links.append(f"https://confluence.url/pages/viewpage.action?pageId={page_id}")
            else:
                other_pdf_sources.add(f"File: {source} Page: {page}")

            # If the source is jira_issues.pdf, store the relevant pages
            if "jira_issues.pdf" in source.lower():
                relevant_jira_pages.add(page - 1)  # Convert to zero-based index

    # Extract Jira issue keys only from relevant pages
    if relevant_jira_pages:
        extracted_jira_keys = extract_jira_keys_from_pdf(JIRA_ISSUES_PDF_PATH, relevant_jira_pages)
        for issue in extracted_jira_keys:
            jira_links.append(f"{JIRA_BASE_URL}{issue}")

    relevant_text = " ".join(documents)

    full_prompt = f"Relevant Information:\n\nUser Query: {user_query}\n\n"
    
    if jira_links:
        full_prompt += f"Related Jira Issues: {', '.join(jira_links)}\n\n"

    full_prompt += "Answer:"
    
    response = generate_answer_with_bedrock(full_prompt, model_id, region)
    print(f"Confluence links: {confluence_links}")
    print(f"Jira links: {jira_links}")

    return response, confluence_links, jira_links, other_pdf_sources
