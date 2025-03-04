import logging

def get_relevant_jira_references(user_query, collection, embedding_function, relevance_threshold=0.75):
    """
    Retrieves only the most relevant Jira references based on semantic similarity.
    Filters out any results with low relevance scores.
    """
    logging.info(f"🔍 Querying ChromaDB for Jira references related to: {user_query}")

    query_embedding = embedding_function([user_query])[0]
    results = collection.query(query_embedding, n_results=5)  # Retrieve top 5 results initially

    if not results or "documents" not in results or not results["documents"]:
        logging.warning("⚠️ No Jira references found in the database.")
        return []

    # Retrieve documents, metadata, and their similarity scores
    documents = results["documents"]
    metadata = results.get("metadatas", [])
    distances = results.get("distances", [])

    filtered_jiras = []
    for i, meta in enumerate(metadata[0]):
        similarity_score = 1 - distances[i]  # Convert distance to similarity
        if similarity_score >= relevance_threshold:
            jira_id = meta.get("source", "Unknown Source")
            jira_title = meta.get("title", "Unknown Title")
            jira_link = f"https://jira.org.com/browse/{jira_id}"

            logging.info(f"✅ Relevant Jira Found: {jira_id} ({jira_title}) - Score: {similarity_score:.2f}")

            filtered_jiras.append(f"[{jira_title}]({jira_link}) (Score: {similarity_score:.2f})")
        else:
            logging.info(f"❌ Excluded Jira: {meta.get('source', 'Unknown Source')} - Score: {similarity_score:.2f}")

    if not filtered_jiras:
        logging.warning("⚠️ No highly relevant Jira references found.")
        return []

    return filtered_jiras
