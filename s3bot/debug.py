confluence_links = []
jira_links = set()
other_pdf_sources = set()

for idx in ranked_indices[:5]:  # Only process metadata for top-ranked documents
    if idx >= len(metadata):  # SAFETY CHECK: Skip if metadata index is out of range
        print(f"Skipping index {idx} as it's out of range for metadata")
        continue

    meta = metadata[idx]
    if isinstance(meta, dict):
        source = meta.get("source", "Unknown Source")
        page = meta.get("page", "Unknown Page")

        # Extract Page ID for Confluence links
        match = re.search(r'(\d{5,})', source)
        if match:
            page_id = match.group(1)
            confluence_links.append(f"{CONFLUENCE_BASE_URL}{page_id}")
        else:
            other_pdf_sources.add(source.lower())

        # Extract Jira Ticket Keys (e.g., "PROJ-1234")
        jira_match = re.findall(r"[A-Z]+-\d+", source)
        if jira_match:
            jira_links.update(jira_match)
