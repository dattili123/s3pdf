To enhance your chatbot to **fetch data from hyperlinks in PDFs referenced by ChromaDB**, follow these steps:

---

## **Steps to Implement**
### **1. Extract URLs from PDFs**
When processing a PDF, identify any hyperlinks inside it and extract them.

### **2. Fetch Content from URLs**
For each extracted URL, determine if it's a PDF:
- If it's a **PDF**, download and process it.
- If it's an **HTML page**, extract meaningful text.

### **3. Index Extracted Content in ChromaDB**
Store the additional content in ChromaDB so it can be retrieved when relevant.

### **4. Modify Response Generation**
If a retrieved document came from a linked URL, reference the original source in the response.

---

## **Implementation Plan**

### **Step 1: Extract URLs from PDFs**
Use `pdfplumber` to find hyperlinks in PDFs:
```python
import pdfplumber
import re

def extract_hyperlinks_from_pdf(pdf_path):
    urls = set()
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                for annotation in page.annots or []:
                    uri = annotation.get("uri")
                    if uri:
                        urls.add(uri)
    except Exception as e:
        print(f"Error extracting hyperlinks from {pdf_path}: {str(e)}")
    return list(urls)
```

---

### **Step 2: Download & Process External URLs**
For each URL:
- If it's a **PDF**, download and process it.
- If it's an **HTML page**, scrape meaningful text.

```python
import requests
from bs4 import BeautifulSoup

def fetch_content_from_url(url, save_dir="./external_pdfs"):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            if "application/pdf" in response.headers.get("Content-Type", ""):
                # Save and process PDF
                pdf_name = url.split("/")[-1]
                pdf_path = f"{save_dir}/{pdf_name}"
                with open(pdf_path, "wb") as f:
                    f.write(response.content)
                print(f"Downloaded PDF: {pdf_path}")
                return {"type": "pdf", "path": pdf_path}

            else:
                # Extract text from HTML
                soup = BeautifulSoup(response.text, "html.parser")
                text = "\n".join([p.get_text() for p in soup.find_all("p")])
                print(f"Extracted text from {url}")
                return {"type": "html", "content": text}

    except Exception as e:
        print(f"Failed to fetch content from {url}: {str(e)}")
    return None
```

---

### **Step 3: Modify ChromaDB Storage to Include Fetched Data**
Modify the function that processes PDFs:

```python
def process_pdf_and_store(pdf_path, embedding_function, collection):
    # Extract text from PDF
    extracted_text = process_large_pdf(pdf_path, batch_size=10)

    # Extract hyperlinks
    hyperlinks = extract_hyperlinks_from_pdf(pdf_path)

    # Fetch content from hyperlinks
    for url in hyperlinks:
        content = fetch_content_from_url(url)
        if content:
            if content["type"] == "pdf":
                process_large_pdf(content["path"], batch_size=10)
            elif content["type"] == "html":
                collection.add(
                    documents=[content["content"]],
                    metadatas=[{"source": url}],
                    ids=[str(hash(content["content"]))]
                )
                print(f"Added HTML content from {url} to ChromaDB")

    # Store original PDF text
    collection.add(
        documents=[extracted_text],
        metadatas=[{"source": pdf_path}],
        ids=[str(hash(extracted_text))]
    )
    print(f"✅ Added {pdf_path} to ChromaDB.")
```

---

### **Step 4: Modify Response Generation to Include Sources**
Modify how responses are constructed:

```python
def query_chromadb_and_generate_response(user_query, embedding_function, collection, model_id, region="us-east-1"):
    query_embedding = embedding_function([user_query])[0]
    results = collection.query(query_embedding, n_results=5)

    if not results or "documents" not in results or not results["documents"]:
        return "No relevant data found in the database."

    # Retrieve relevant text chunks and metadata
    documents = [doc for sublist in results["documents"] for doc in sublist]
    metadata = results.get("metadatas", [])

    reference_links = []
    for meta in metadata[0]:
        if isinstance(meta, dict):
            source = meta.get("source", "Unknown Source")
            if source.startswith("http"):  # If content came from a URL
                reference_links.append(f"[Source]({source})")
            else:
                reference_links.append(f"File: {source}")

    # Generate response with references
    relevant_text = " ".join(documents)
    response = generate_answer_with_bedrock(f"{relevant_text}\n\nQuery: {user_query}", model_id, region)

    # Append sources to response
    reference_section = "\n\n🔗 Sources:\n" + "\n".join(reference_links)
    return response + reference_section
```

---

## **Final Outcome**
✅ **If ChromaDB refers to a PDF, it will check for external hyperlinks in it.**  
✅ **If a hyperlink points to a PDF, it downloads and indexes that PDF.**  
✅ **If a hyperlink points to a web page, it extracts text and indexes it.**  
✅ **The chatbot response will include references to these external sources.**  

---

### **Example Response**
```
Answer: S3GO can be used for uploading and downloading files between S3 and on-prem servers.
It supports both LDAP ID and NUID authentication.

🔗 Sources:
- [Source](https://confluence.example.com/page?id=12345)
- File: ./pdf_dir/setup_s3go.pdf
- [Source](https://docs.aws.amazon.com/s3/api.pdf)
```

Now, your chatbot dynamically **fetches and references external sources** found inside PDFs. 🚀 Let me know if you need further refinements!
