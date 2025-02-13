CHROMADB_PATH = "./chromadb"
if not os.path.exists(CHROMADB_PATH):
    os.makedirs(CHROMADB_PATH)
chroma_client = chromadb.PersistentClient(path=CHROMADB_PATH)

# Get or create collection
embedding_function = TitanEmbeddingFunction(model_id="amazon.titan-embed-text-v2:0")
collection = chroma_client.get_or_create_collection(name="my_collection", embedding_function=embedding_function)

# Efficient PDF Processing
def process_large_pdf(pdf_path, batch_size=10, chunk_size=800, chunk_overlap=25):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    batch = []  # Store chunks before adding to ChromaDB
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                chunks = text_splitter.split_text(text)  # Split text into smaller chunks
                for chunk in chunks:
                    batch.append({"text": chunk, "metadata": {"source": pdf_path, "page": page_num + 1}})
                
                # Process in batches to avoid memory overflow
                if len(batch) >= batch_size:
                    store_embeddings_in_chromadb(batch, embedding_function)
                    batch = []  # Clear batch from memory

        # Process any remaining chunks
        if batch:
            store_embeddings_in_chromadb(batch, embedding_function)

# Store Embeddings Efficiently in ChromaDB
def store_embeddings_in_chromadb(batch, embedding_function):
    documents = [item["text"] for item in batch]
    metadatas = [item["metadata"] for item in batch]
    ids = [str(hash(item["text"])) for item in batch]

    # Store in ChromaDB (Chunked)
    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    print(f"✅ Added {len(batch)} chunks to ChromaDB.")

# Process All PDFs in a Directory
def store_all_pdfs_in_chromadb(pdf_dir: str, embedding_function):
    """Ensure pdf_dir is a string, not a list"""
    if not isinstance(pdf_dir, str):
        raise TypeError(f"Expected pdf_dir to be a string, got {type(pdf_dir)} instead.")
    
    for pdf_file in os.listdir(pdf_dir):
        if pdf_file.endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, pdf_file)
            print(f"Processing new PDF: {pdf_file}")
            try:
                process_large_pdf(pdf_path, batch_size=10)
            except Exception as e:
                print(f"Error processing PDF {pdf_file}: {str(e)}")
