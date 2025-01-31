def store_embeddings_in_chromadb(pdf_dir, embedding_function):
    client = chromadb.PersistentClient(path="./chromadb")
    collection = client.get_or_create_collection(name="my_collection", embedding_function=embedding_function)

    # Get existing metadata for all stored chunks
    existing_data = collection.get(include=["metadatas"])
    existing_files = {metadata.get("source") for metadata in existing_data["metadatas"] if "source" in metadata}

    # Iterate over all PDFs in the directory
    for pdf_file in os.listdir(pdf_dir):
        if pdf_file.endswith(".pdf"):
            if pdf_file in existing_files:  # Skip if already processed
                print(f"Skipping existing PDF: {pdf_file}")
                continue

            pdf_path = os.path.join(pdf_dir, pdf_file)
            print(f"Processing new PDF: {pdf_file}")
            try:
                chunks = read_and_chunk_pdfs(pdf_path)  # Create chunks from the new PDF
                for chunk in chunks:
                    chunk_id = str(hash(chunk.page_content))  # Generate a unique ID for the chunk
                    collection.add(
                        documents=[chunk.page_content],
                        metadatas=[{"id": chunk_id, "source": pdf_file, **chunk.metadata}],
                        ids=[chunk_id]
                    )
            except Exception as e:
                print(f"Error processing PDF {pdf_file}: {e}")
    return collection

def read_and_chunk_pdfs(pdf_path, chunk_size=800, chunk_overlap=25):
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    all_chunks = []

    try:
        pdf_reader = PdfReader(pdf_path)
        for page_num, page in enumerate(pdf_reader.pages):
            text = page.extract_text()
            if text:
                split_docs = text_splitter.create_documents(
                    texts=[text],
                    metadatas=[{"page": page_num + 1}]
                )
                all_chunks.extend(split_docs)
    except Exception as e:
        print(f"Error reading {pdf_path}: {str(e)}")

    return all_chunks

if "collection" not in st.session_state:
    with st.spinner("Initializing ChromaDB..."):
        embedding_function = TitanEmbeddingFunction(model_id="amazon.titan-embed-text-v2:0")
        client = chromadb.PersistentClient(path="./chromadb")
        collection = client.get_or_create_collection(name="my_collection", embedding_function=embedding_function)

        # Process PDFs and add embeddings only for new files
        st.session_state.collection = store_embeddings_in_chromadb(PDF_DIR, embedding_function)
        st.success("Embeddings have been updated for new PDFs!")
else:
    st.success("Existing embeddings found. Ready to use!")
