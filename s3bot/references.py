import numpy as np
import re
from sklearn.metrics.pairwise import cosine_similarity

def query_chromadb_and_generate_response(user_query, embedding_function, collection, model_id, region="us-east-1"):
    # Generate query embedding
    query_embedding = embedding_function([user_query])
    
    # Query ChromaDB for relevant documents
    results = collection.query(query_embedding, n_results=10, include=["documents", "metadatas", "embeddings"])  # Increase recall
    
    if not results or "documents" not in results or not results["documents"]:
        return "No relevant data found in the database."

    # Retrieve text chunks, metadata, and embeddings
    documents = [doc for sublist in results["documents"] for doc in sublist]
    metadata = results.get("metadatas", [])
    doc_embeddings = np.array(results.get("embeddings", []))  # Extract document embeddings
    query_vector = np.array(query_embedding).reshape(1, -1)  # Ensure proper shape

    # Compute Cosine Similarity
    similarity_scores = cosine_similarity(query_vector, doc_embeddings)[0]
    ranked_indices = np.argsort(similarity_scores)[::-1]  # Rank by descending similarity

    # Filter documents based on similarity threshold (0.75 recommended)
    THRESHOLD = 0.75
    ranked_documents = []
    for idx in ranked_indices:
        if similarity_scores[idx] >= THRESHOLD:
            ranked_documents.append((documents[idx], similarity_scores[idx]))

    # If no documents meet the threshold, fallback to top N results
    if not ranked_documents:
        ranked_documents = [(documents[idx], similarity_scores[idx]) for idx in ranked_indices[:5]]

    # Extract most relevant text
    relevant_text = "\n".join([doc[0] for doc in ranked_documents[:5]])  # Take top 5 ranked

    # Process metadata for Confluence & Jira links
    confluence_links = []
    jira_links = set()
    other_pdf_sources = set()

    for idx in ranked_indices[:5]:  # Only process metadata for top-ranked documents
        meta = metadata[idx]
        if isinstance(meta, dict):
            source = meta.get("source", "Unknown Source")
            page = meta.get("page", "Unknown Page")

            # Extract Page ID for Confluence links
            match = re.search(r'(\d{5,})', source)
            if match:
                page_id = match.group(1)
                confluence_links.append(f"{CONFLUENCE_BASE_URL}{page_id}")
            else:
                other_pdf_sources.add(source.lower())

            # Extract Jira Ticket Keys (e.g., "PROJ-1234")
            jira_match = re.findall(r"[A-Z]+-\d+", source)
            if jira_match:
                jira_links.update(jira_match)

    # Generate response using Amazon Bedrock
    full_prompt = f"User Query: {user_query}\n\nContext:\n{relevant_text}\n\nAnswer:"
    response = response_regeneration_function(full_prompt, model_id, region)

    print(f"Final Jira Links: {jira_links}")
    print(f"Final Confluence Links: {confluence_links}")

    return response, confluence_links, other_pdf_sources, list(jira_links)
