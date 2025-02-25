import re

def query_chromadb_and_generate_response(user_query, embedding_function, collection, model_id, region="us-east-1"):
    query_embedding = embedding_function([user_query])[0]
    results = collection.query(query_embedding, n_results=5)

    if not results or "documents" not in results or not results["documents"]:
        return "No relevant data found in the database.", [], []

    # Retrieve relevant text chunks and metadata
    documents = [doc for sublist in results["documents"] for doc in sublist]
    metadata = results.get("metadatas", [])
    print(f"Metadata is as follows: {metadata}")

    confluence_links = []
    jira_links = []
    other_pdf_sources = set()

    JIRA_BASE_URL = "https://8443/browse/"  # Update this based on your actual Jira URL

    for meta in metadata[0]:
        if isinstance(meta, dict):  # Ensure metadata is a dictionary
            source = meta.get("source", "Unknown Source")
            page = meta.get("page", "Unknown Page")
            print(f"Processing metadata: source=({source}), page=({page})")

            # Extract Page ID from Filename (Expected format: {page_id}_{title}.pdf)
            match = re.match(r".*/(\d+)_.*\.pdf", source)  # Adjusted regex

            if match:
                page_id = match.group(1)
                print(f"Extracted Page ID: {page_id}")
                f = f"https://confluence.url/pages/viewpage.action?pageId={page_id}"
                confluence_links.append(f)
            else:
                print(f"Page ID not found in source: {source}")
                other_pdf_sources.add(f"File: {source} Page: {page}")

            # Extract Jira issue keys from text
            text = meta.get("text", "")
            found_issues = re.findall(r'\b[A-Z]+-\d+\b', text)  # Matches Jira issue format (e.g., PANTHER-2462)
            for issue in found_issues:
                jira_links.append(f"{JIRA_BASE_URL}{issue}")

    relevant_text = " ".join(documents)

    full_prompt = f"Relevant Information:\n\nUser Query: {user_query}\n\n"
    
    if jira_links:
        jira_references = ", ".join(jira_links)
        full_prompt += f"Related Jira Issues: {jira_references}\n\n"

    full_prompt += "Answer:"
    
    response = generate_answer_with_bedrock(full_prompt, model_id, region)
    print(f"Confluence links: {confluence_links}")
    print(f"Jira links: {jira_links}")

    return response, confluence_links, jira_links, other_pdf_sources
