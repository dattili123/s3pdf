if "collection" not in st.session_state:
    with st.spinner("Initializing ChromaDB..."):
        embedding_function = TitanEmbeddingFunction(model_id="amazon.titan-embed-text-v2:0")
        client = chromadb.PersistentClient(path="./chromadb")
        collection = client.get_or_create_collection(name="my_collection", embedding_function=embedding_function)
        existing_data = collection.get(include=["metadatas"])

        if not existing_data["metadatas"]:
            st.info("Embeddings not found. Generating new embeddings...")
            chunks = read_and_chunk_pdf(PDF_PATH)
            st.session_state.collection = store_embeddings_in_chromadb(chunks, embedding_function)
            st.success("Embeddings have been generated and stored!")
        else:
            st.session_state.collection = collection
            st.success("Existing embeddings found. Ready to use!")
