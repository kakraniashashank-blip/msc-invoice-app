import concurrent.futures
import time
import requests
import urllib.parse
import os
import config
from typing import Callable

def fetch_documents(urls: list[str], progress_callback: Callable[[int, int], None] = None) -> list[dict]:
    """
    Fetches confirmed URLs concurrently.

    Args:
        urls (list[str]): List of URLs to fetch.
        progress_callback (callable, optional): Called after each fetch with (completed, total).

    Returns:
        list[dict]: List of dictionaries containing fetch results.
    """
    results = []
    total = len(urls)
    completed = 0

    def fetch_single_url(url: str) -> dict:
        result = {
            'url': url,
            'content_type': 'html',  # default
            'content': None,
            'filename': os.path.basename(urllib.parse.urlparse(url).path) or 'index.html',
            'error': None
        }
        
        try:
            # Introduce delay to avoid overwhelming the server
            time.sleep(config.FETCH_DELAY_SECONDS)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5'
            }
            # Use stream=True to check Content-Length for large PDFs before downloading all
            response = requests.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT_SECONDS, stream=True)
            response.raise_for_status()
            
            content_type_header = response.headers.get('Content-Type', '').lower()
            
            if 'application/pdf' in content_type_header or url.lower().endswith('.pdf'):
                result['content_type'] = 'pdf'
                
                # Check size if available
                content_length = response.headers.get('Content-Length')
                if content_length:
                    size_mb = int(content_length) / (1024 * 1024)
                    if size_mb > config.MAX_PDF_SIZE_MB:
                        result['error'] = f"PDF size ({size_mb:.2f} MB) exceeds maximum allowed ({config.MAX_PDF_SIZE_MB} MB)"
                        return result
                        
                # Read content
                result['content'] = response.content
            else:
                result['content_type'] = 'html'
                # For HTML we want the text
                result['content'] = response.text
                
        except requests.RequestException as e:
            result['error'] = str(e)
        except Exception as e:
            result['error'] = f"Unexpected error: {str(e)}"
            
        return result

    with concurrent.futures.ThreadPoolExecutor(max_workers=config.MAX_CONCURRENT_FETCHES) as executor:
        # Submit all tasks
        future_to_url = {executor.submit(fetch_single_url, url): url for url in urls}
        
        # Process completed tasks
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                data = future.result()
            except Exception as exc:
                data = {
                    'url': url,
                    'content_type': 'html',
                    'content': None,
                    'filename': '',
                    'error': f"Thread pool exception: {exc}"
                }
            
            results.append(data)
            completed += 1
            if progress_callback:
                progress_callback(completed, total)

    return results
