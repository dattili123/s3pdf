import re

for meta in metadata:
    if isinstance(meta, dict):  # Ensure metadata is a dictionary
        source = meta.get("source", "Unknown Source")
        page = meta.get("page", "Unknown Page")

        print(f"Processing metadata: source={source}, page={page}")

        # Extract Page ID from Filename (Expected format: {page_id}_{title}.pdf)
        match = re.match(r".*/(\d+)_.*\.pdf", source)  # Adjusted regex
        if match:
            page_id = match.group(1)
            print(f"Extracted Page ID: {page_id}")
            f = f"[{source.replace('./pdf_dir/', '')}]({CONFLUENCE_BASE_URL}{page_id})"
            confluence_links.append(f)
        else:
            print(f"Page ID not found in source: {source}")
            other_pdf_sources.add(f"**File:** {source} **Page:** {page}")

print(f"Final confluence_links: {confluence_links}")
