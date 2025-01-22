def store_embeddings_in_chromadb(chunks, embedding_function):
    client = PersistentClient(path="./chromadb")
    collection = client.get_or_create_collection(name="my_collection", embedding_function=embedding_function)

    existing_ids = set(collection.get_ids())  # Get existing IDs
    for idx, chunk in enumerate(chunks):
        chunk_id = str(idx)
        if chunk_id not in existing_ids:  # Skip if already added
            collection.add(
                documents=[chunk.page_content],
                metadatas=[chunk.metadata],
                ids=[chunk_id]
            )


if __name__ == "__main__":
    pdf_path = "path_to_your_pdf.pdf"
    embedding_function = TitanEmbeddingFunction(model_id="amazon.titan-embed-text-v2:0")

    # Initialize ChromaDB client
    client = PersistentClient(path="./chromadb")
    collection = client.get_or_create_collection(name="my_collection", embedding_function=embedding_function)

    # Check if collection is empty
    if not collection.get_ids():
        print("Collection is empty. Generating embeddings...")
        chunks = read_and_chunk_pdf(pdf_path)
        store_embeddings_in_chromadb(chunks, embedding_function)
    else:
        print("Collection already populated. Skipping embedding generation.")

    # Chatbot loop
    model_id = "your-llm-model-id"
    region = "us-east-1"
    while True:
        user_query = input("Ask your question (or type 'exit' to quit): ")
        if user_query.lower() == "exit":
            print("Exiting chatbot. Goodbye!")
            break
        response = query_chromadb_and_generate_response(user_query, embedding_function, collection, model_id, region)
        print("Chatbot Response:", response)
