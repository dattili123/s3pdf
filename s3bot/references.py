import logging

def query_chromadb_and_generate_response(user_query, embedding_function, collection, model_id, region="us-east-1", relevance_threshold=0.75):
    """
    Queries ChromaDB for the most relevant Jira references and generates a response.
    Filters out irrelevant Jira issues based on a similarity threshold.
    """
    logging.info(f"🔍 Querying ChromaDB for: {user_query}")

    query_embedding = embedding_function([user_query])[0]
    results = collection.query(query_embedding, n_results=5)  # Retrieve top 5 results initially

    if not results or "documents" not in results or not results["documents"]:
        return "No relevant data found in the database."

    # Retrieve documents, metadata, and similarity scores
    documents = [doc for sublist in results["documents"] for doc in sublist]
    metadata = results.get("metadatas", [])
    distances = results.get("distances", [])

    logging.info(f"Retrieved {len(metadata[0])} potential Jira references.")

    confluence_links = []
    relevant_jira_references = []  # Store only relevant JIRA links
    other_pdf_sources = set()

    for i, meta in enumerate(metadata[0]):
        similarity_score = 1 - distances[i]  # Convert distance to similarity

        if isinstance(meta, dict):
            source = meta.get("source", "Unknown Source")
            page = meta.get("page", "Unknown Page")
            
            # Extract Jira ID (Expected format: PANTHER-XXXX)
            jira_id = meta.get("source", "").strip()
            jira_title = meta.get("title", "Unknown Title")
            jira_link = f"https://jira.org.com/browse/{jira_id}"

            if "PANTHER" in jira_id:  # Check if it's a Jira ticket
                if similarity_score >= relevance_threshold:
                    relevant_jira_references.append(f"[{jira_title}]({jira_link}) (Score: {similarity_score:.2f})")
                    logging.info(f"✅ Adding relevant Jira: {jira_id} ({jira_title}) - Score: {similarity_score:.2f}")
                else:
                    logging.info(f"❌ Excluding Jira: {jira_id} ({jira_title}) - Score: {similarity_score:.2f}")

            else:
                match = re.match(r".*/(\d+)_.*\.pdf", source)  # Extract Confluence Page ID
                if match:
                    page_id = match.group(1)
                    confluence_links.append(f"https://confluence.url/{page_id}")
                else:
                    other_pdf_sources.add(f"File: {source} Page: {page}")

    # Ensure only relevant Jiras are included in the response
    jira_references_section = "\n\n🔗 Relevant Jira References:\n" + "\n".join(relevant_jira_references) if relevant_jira_references else "\n\n⚠️ No highly relevant Jira references found."

    # Generate Bedrock response
    relevant_text = " ".join(documents)
    full_prompt = f"Relevant Information:\n\nUser Query: {user_query}\n\nAnswer:"
    response = generate_answer_with_bedrock(full_prompt, model_id, region)

    # Append Jira references to the final response
    final_response = f"{response}{jira_references_section}"
    logging.info("✅ Final Response Generated.")

    return final_response, confluence_links, other_pdf_sources
