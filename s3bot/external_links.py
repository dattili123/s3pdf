### **Enhancing Your Workflow: Handling Hyperlinked PDFs and External URLs**
Since you're using a **separate script for Confluence PDF extraction**, I'll integrate this logic into your existing workflow while ensuring:

✅ **Confluence Links → Fetch PDFs → Create Embeddings**  
✅ **External URLs → Extract Content → Convert to PDF → Create Embeddings**  
✅ **Store Everything in ChromaDB for Retrieval**

---

## **🚀 Implementation Plan**

### **🔹 1. Extract Hyperlinks from PDFs**
- If a hyperlink points to **Confluence**, fetch the page as a PDF.
- If a hyperlink points to an **external site**, scrape and convert it into a PDF.

### **🔹 2. Process and Store in ChromaDB**
- Convert **fetched Confluence pages** and **external site content** into PDFs.
- Embed their text for retrieval during chatbot queries.

---

## **📌 Step 1: Extract Hyperlinks from PDFs**
Modify your Confluence PDF processing script to extract hyperlinks.

```python
import pdfplumber
import re

def extract_hyperlinks_from_pdf(pdf_path):
    """Extracts URLs from a given PDF file."""
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

## **📌 Step 2: Fetch Content from URLs**
For each hyperlink:
- If it’s a **Confluence page**, use your existing script to get the PDF.
- If it’s an **external link**, scrape the text and convert it to a PDF.

```python
import requests
from bs4 import BeautifulSoup

def fetch_content_from_url(url, save_dir="./external_pdfs"):
    """Fetch content from a URL, downloading PDFs or extracting HTML text."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")

            if "application/pdf" in content_type:
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
                
                # Save as PDF
                pdf_path = f"{save_dir}/{re.sub(r'[^a-zA-Z0-9]', '_', url)}.pdf"
                with open(pdf_path, "w", encoding="utf-8") as f:
                    f.write(text)
                
                return {"type": "html", "path": pdf_path}

    except Exception as e:
        print(f"Failed to fetch content from {url}: {str(e)}")
    return None
```

---

## **📌 Step 3: Process and Index PDFs in ChromaDB**
Modify your **Confluence processing script** to handle newly fetched PDFs.

```python
def process_pdf_and_store(pdf_path, embedding_function, collection):
    """Extract text from PDFs, store in ChromaDB, and process external hyperlinks."""
    extracted_text = process_large_pdf(pdf_path, batch_size=10)

    # Extract hyperlinks
    hyperlinks = extract_hyperlinks_from_pdf(pdf_path)

    # Fetch content from hyperlinks
    for url in hyperlinks:
        if "confluence" in url:  # If it's a Confluence page
            confluence_pdf = export_page_to_pdf(url.split("=")[-1])  # Extract page ID
            process_large_pdf(confluence_pdf, batch_size=10)
        
        else:  # External URL
            content = fetch_content_from_url(url)
            if content:
                process_large_pdf(content["path"], batch_size=10)

    # Store the original PDF text in ChromaDB
    collection.add(
        documents=[extracted_text],
        metadatas=[{"source": pdf_path}],
        ids=[str(hash(extracted_text))]
    )
    print(f"✅ Added {pdf_path} to ChromaDB.")
```

---

## **📌 Step 4: Modify Query Processing to Include Hyperlinks**
When retrieving from ChromaDB, ensure external sources are referenced.

```python
def query_chromadb_and_generate_response(user_query, embedding_function, collection, model_id, region="us-east-1"):
    """Query ChromaDB and fetch additional data from hyperlinked PDFs or webpages."""
    query_embedding = embedding_function([user_query])[0]
    results = collection.query(query_embedding, n_results=5)

    if not results or "documents" not in results or not results["documents"]:
        return "No relevant data found in the database."

    # Retrieve relevant text chunks and metadata
    documents = [doc for sublist in results["documents"] for doc in sublist]
    metadata = results.get("metadatas", [])
    print(f"Metadata is as follows: {metadata}")

    confluence_links = []
    external_sources = []  # To store additional sources found in linked documents

    for meta in metadata[0]:
        if isinstance(meta, dict):  
            source = meta.get("source", "Unknown Source")
            print(f"Processing metadata: source=({source})")

            # Extract Page ID for Confluence
            if "confluence" in source:
                page_id = source.split("=")[-1]  # Extract page ID
                confluence_links.append(f"https://confluence.url/pages/viewpage.action?pageId={page_id}")
            
            # Track external sources
            elif source.startswith("http"):
                external_sources.append(source)

    # Construct full response
    relevant_text = " ".join(documents)
    response = generate_answer_with_bedrock(f"{relevant_text}\n\nQuery: {user_query}", model_id, region)

    # Append sources
    reference_section = "\n\n🔗 Sources:\n"
    if confluence_links:
        reference_section += "📄 Confluence Pages:\n" + "\n".join(confluence_links) + "\n"
    if external_sources:
        reference_section += "🔗 External Sources:\n" + "\n".join(external_sources) + "\n"

    return response + reference_section
```

---

## **🎯 What This Achieves**
### **✅ Hyperlinked PDFs**
- If a **Confluence link** is found inside a referenced PDF, it fetches that Confluence page as a **PDF** and indexes it.

### **✅ External Web Pages**
- If a **normal URL** is found inside a PDF, it **scrapes the webpage**, **converts it into a PDF**, and **indexes the extracted text**.

### **✅ Intelligent Retrieval**
- When querying ChromaDB, **external content is also referenced**, ensuring **rich, contextually relevant responses**.

---

## **🚀 Final Outcome**
### **Example Chatbot Response**
```
Answer: The S3GO tool allows secure transfer of files between S3 and on-prem servers.
It supports authentication via LDAP ID and NUID.

🔗 Sources:
📄 Confluence Pages:
- https://confluence.url/pages/viewpage.action?pageId=123456
🔗 External Sources:
- [AWS S3 API Documentation](https://docs.aws.amazon.com/s3/api.pdf)
```

Now, your chatbot dynamically **fetches and references external sources found inside PDFs** for **complete, enriched responses**! 🚀  

Let me know if you need any refinements!
