import re
import streamlit as st

CONFLUENCE_BASE_URL = "https://confluence.organization.com/pages/viewpage.action?pageId="

def query_chromadb_and_generate_response(user_query, embedding_function, collection, model_id, region="us-east-1"):
    query_embedding = embedding_function([user_query])[0]
    results = collection.query(query_embedding, n_results=5)

    if not results or "documents" not in results or not results["documents"]:
        return "No relevant data found in the database.", []

    # Retrieve relevant text chunks and metadata
    documents = [doc for sublist in results["documents"] for doc in sublist]
    metadata = results.get("metadatas", [])

    confluence_links = []
    other_pdf_sources = set()

    for meta in metadata:
        if isinstance(meta, dict):  # Ensure metadata is a dictionary
            source = meta.get("source", "Unknown Source")
            page = meta.get("page", "Unknown Page")

            # Extract Page ID from Filename (Format: "{page_id}_{title}.pdf")
            match = re.match(r"(\d+)_.*\.pdf", source)
            if match:
                page_id = match.group(1)  # Extract Page ID
                confluence_links.append(
                    f"- 📄 [{source.replace('_', ' ')}]({CONFLUENCE_BASE_URL}{page_id}) (Page {page})"
                )
            else:
                other_pdf_sources.add(f"- 📂 **File:** {source} | **Page:** {page}")

    relevant_text = " ".join(documents)
    full_prompt = f"Relevant Information: {relevant_text}\n\nUser Query: {user_query}\n\nAnswer:"
    response = generate_answer_with_bedrock(full_prompt, model_id, region)

    return response, confluence_links, other_pdf_sources

# Streamlit UI
if st.button("Submit"):
    with st.spinner("Processing..."):
        response, confluence_links, other_pdf_sources = query_chromadb_and_generate_response(
            user_query,
            TitanEmbeddingFunction(model_id="amazon.titan-embed-text-v2:0"),
            st.session_state.collection,
            "anthropic.claude-3-5-sonnet-20240620-v1:0"
        )

        # Append References to Response
        reference_section = "\n\n### 🔗 References:\n"
        if confluence_links:
            reference_section += "**📄 Confluence Sources:**\n" + "\n".join(confluence_links) + "\n"
        if other_pdf_sources:
            reference_section += "**📂 Other PDF Sources:**\n" + "\n".join(other_pdf_sources) + "\n"

        final_response = f"{response}{reference_section}"
        
        # Display Response
        st.text_area("Chatbot Response:", value=final_response, height=300)
