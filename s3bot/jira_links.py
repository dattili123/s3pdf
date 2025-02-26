import re

JIRA_BASE_URL = "https://8443/browse/"

def extract_jira_keys_from_response(response_text):
    """
    Extracts Jira issue keys (e.g., PANTHER-2219) from the Bedrock response.
    """
    return list(set(re.findall(r'\b[A-Z]+-\d+\b', response_text)))  # Unique Jira keys

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
    other_pdf_sources = set()

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

    relevant_text = " ".join(documents)

    full_prompt = f"Relevant Information:\n\n{relevant_text}\n\nUser Query: {user_query}\n\nAnswer:"
    
    response = generate_answer_with_bedrock(full_prompt, model_id, region)
    print(f"Bedrock Response: {response}")

    # Extract Jira keys from the Bedrock response
    jira_keys_from_response = extract_jira_keys_from_response(response)

    # Generate Jira links only for extracted keys
    jira_links = [f"{JIRA_BASE_URL}{key}" for key in jira_keys_from_response]

    print(f"Final Jira Links: {jira_links}")
    print(f"Confluence links: {confluence_links}")
    print(f"Other PDF Sources: {other_pdf_sources}")

    return response, confluence_links, jira_links, other_pdf_sources
