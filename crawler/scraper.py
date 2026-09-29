import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
import config

def scrape_seed_url(url: str) -> list[dict]:
    """
    Scrapes a seed URL and extracts all links with context.
    
    Fetches the page, extracts all <a> tags. For each link, captures:
    - url: absolute URL
    - anchor_text: the link text
    - context: surrounding text (parent paragraph or 200 chars around the link)
    - content_type_hint: 'pdf' if URL ends in .pdf, 'html' otherwise
    Filters out links matching SKIP_URL_PATTERNS from config.py.
    Deduplicates by URL.
    
    Args:
        url (str): The seed URL to scrape.
        
    Returns:
        list[dict]: A list of dictionaries containing extracted link information.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching seed URL {url}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    extracted_links = []
    seen_urls = set()

    for a_tag in soup.find_all('a'):
        href = a_tag.get('href')
        if not href:
            continue

        absolute_url = urllib.parse.urljoin(url, href)

        # Skip already seen URLs
        if absolute_url in seen_urls:
            continue

        # Check skip patterns
        skip = False
        for pattern in config.SKIP_URL_PATTERNS:
            if re.search(pattern, absolute_url, re.IGNORECASE):
                skip = True
                break
        if skip:
            continue
            
        seen_urls.add(absolute_url)

        anchor_text = a_tag.get_text(strip=True)
        
        # Get context: parent paragraph text, or surrounding text if no parent p
        parent_p = a_tag.find_parent('p')
        if parent_p:
            context = parent_p.get_text(strip=True)
        else:
            # Fallback to surrounding sibling text/content
            parent = a_tag.parent
            if parent:
                 full_text = parent.get_text(strip=True)
                 # find the anchor text in the full text and get 200 chars around it
                 idx = full_text.find(anchor_text)
                 if idx != -1:
                     start = max(0, idx - 100)
                     end = min(len(full_text), idx + len(anchor_text) + 100)
                     context = full_text[start:end]
                 else:
                     context = full_text[:200]
            else:
                 context = ""

        content_type_hint = 'pdf' if absolute_url.lower().endswith('.pdf') else 'html'

        extracted_links.append({
            'url': absolute_url,
            'anchor_text': anchor_text,
            'context': context,
            'content_type_hint': content_type_hint
        })

    return extracted_links
