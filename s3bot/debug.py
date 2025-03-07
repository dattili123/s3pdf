# Generate query embedding
query_embedding = embedding_function([user_query])

# Ensure query_embedding is a 2D array
query_embedding = np.array(query_embedding)
print(f"Query Embedding Shape Before Reshape: {query_embedding.shape}")

if query_embedding.ndim == 3:  # Fix case where it's (1, 1, embedding_dim)
    query_embedding = query_embedding.squeeze(axis=1)  # Remove extra dimension

query_vector = query_embedding.reshape(1, -1)
print(f"Query Vector Shape After Reshape: {query_vector.shape}")

# Query ChromaDB for relevant documents
results = collection.query(query_vector, n_results=10, include=["documents", "metadatas", "embeddings"])

if not results or "documents" not in results or not results["documents"]:
    return "No relevant data found in the database."

# Retrieve document embeddings
doc_embeddings = np.array(results.get("embeddings", []))
print(f"Document Embeddings Shape Before Reshape: {doc_embeddings.shape}")

# Ensure document embeddings are properly shaped
if doc_embeddings.ndim == 3:
    doc_embeddings = doc_embeddings.squeeze(axis=1)  # Remove extra dimension

print(f"Document Embeddings Shape After Reshape: {doc_embeddings.shape}")

# Compute Cosine Similarity
similarity_scores = cosine_similarity(query_vector, doc_embeddings)[0]
