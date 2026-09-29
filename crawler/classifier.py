import json
import re
from google import genai
import config

def classify_links(links: list[dict], seed_url: str, api_key: str) -> list[dict]:
    """
    Uses Gemini LLM to classify discovered links into categories.

    Args:
        links (list[dict]): List of links extracted by the scraper.
        seed_url (str): The seed URL used for context.
        api_key (str): The Gemini API key.

    Returns:
        list[dict]: Original links annotated with category, confidence, reason, recommended.
    """
    if not links:
        return []

    client = genai.Client(api_key=api_key)
    
    # Prepare links for JSON stringification
    links_data = [{"url": link["url"], "anchor_text": link["anchor_text"], "context": link.get("context", "")[:200]} for link in links]
    links_json_str = json.dumps(links_data, indent=2)

    prompt = config.LINK_CLASSIFICATION_PROMPT.format(
        seed_url=seed_url,
        links_json=links_json_str
    )

    import time
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=config.CLASSIFICATION_MODEL,
                contents=[prompt]
            )
            response_text = response.text
            break
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print(f"Rate limited during classification. Retrying in 20 seconds... (Attempt {attempt+1}/3)")
                time.sleep(20)
                continue
            else:
                print(f"Error calling Gemini API: {e}")
                return _fallback_classification(links)
    else:
        print("Failed to classify after 3 attempts due to rate limits.")
        return _fallback_classification(links)

    parsed_json = None
    try:
        parsed_json = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to clean it (strip markdown fences)
        clean_text = re.sub(r'```json\n|```\n?', '', response_text).strip()
        try:
            parsed_json = json.loads(clean_text)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {e}")
            print(f"Raw response: {response_text}")
            return _fallback_classification(links)
    
    if not isinstance(parsed_json, list):
        print("Expected a JSON list from the model, but got something else.")
        return _fallback_classification(links)

    # Merge classifications back to links
    classification_map = {item.get('url'): item for item in parsed_json if isinstance(item, dict) and 'url' in item}
    
    classified_links = []
    for link in links:
        annotated_link = link.copy()
        url = link['url']
        if url in classification_map:
            c_data = classification_map[url]
            annotated_link['category'] = c_data.get('category', 'OTHER_RELEVANT')
            annotated_link['confidence'] = c_data.get('confidence', 0.5)
            annotated_link['reason'] = c_data.get('reason', 'Classified by LLM')
            annotated_link['recommended'] = c_data.get('recommended', False)
        else:
             annotated_link['category'] = 'OTHER_RELEVANT'
             annotated_link['confidence'] = 0.0
             annotated_link['reason'] = 'LLM missed this link'
             annotated_link['recommended'] = False
        classified_links.append(annotated_link)

    return classified_links

def _fallback_classification(links: list[dict]) -> list[dict]:
    """Helper to apply fallback classification when LLM fails."""
    fallback_links = []
    for link in links:
        fallback_link = link.copy()
        fallback_link['category'] = 'OTHER_RELEVANT'
        fallback_link['confidence'] = 0.1
        fallback_link['reason'] = 'Fallback due to LLM error'
        fallback_link['recommended'] = False
        fallback_links.append(fallback_link)
    return fallback_links
