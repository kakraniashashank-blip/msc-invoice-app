import time
import logging
from typing import List

from google import genai
from google.genai import types

import config

logger = logging.getLogger(__name__)

def get_client(api_key: str) -> genai.Client:
    """
    Creates and returns a Gemini genai.Client.
    
    Args:
        api_key (str): The Google API key.
        
    Returns:
        genai.Client: The initialized client.
    """
    return genai.Client(api_key=api_key)

def embed_documents(client: genai.Client, texts: List[str], batch_size: int = 100) -> List[List[float]]:
    """
    Embeds a list of document texts using Gemini's batchEmbedContents REST API.
    
    Args:
        client (genai.Client): The initialized Gemini client.
        texts (List[str]): List of texts to embed.
        batch_size (int, optional): Number of documents per batch. Defaults to 100.
        
    Returns:
        List[List[float]]: A flat list of embedding vectors.
    """
    import requests
    all_embeddings = []
    
    # Extract API key safely from the client
    api_key = getattr(client, 'api_key', None) or getattr(getattr(client, '_api_client', None), 'api_key', None)
    if not api_key:
        raise ValueError("Could not extract API key from Gemini client")
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.EMBEDDING_MODEL}:batchEmbedContents?key={api_key}"
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        payload = {
            "requests": [
                {
                    "model": f"models/{config.EMBEDDING_MODEL}",
                    "content": {"parts": [{"text": text}]},
                    "taskType": "RETRIEVAL_DOCUMENT",
                    "outputDimensionality": config.EMBEDDING_DIMENSIONS
                }
                for text in batch
            ]
        }
        
        max_retries = 5
        retry_delay = 5.0
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, json=payload, timeout=60)
                response.raise_for_status()
                data = response.json()
                
                batch_embeddings = [emb['values'] for emb in data.get('embeddings', [])]
                if len(batch_embeddings) != len(batch):
                    raise ValueError(f"Expected {len(batch)} embeddings, got {len(batch_embeddings)}")
                    
                all_embeddings.extend(batch_embeddings)
                break
                
            except Exception as e:
                if "429" in str(e) or (hasattr(e, 'response') and e.response is not None and e.response.status_code == 429):
                    if attempt < max_retries - 1:
                        logger.warning(f"Rate limited embedding batch. Retrying in {retry_delay}s... (Attempt {attempt+1}/{max_retries})")
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                
                logger.warning(f"Error embedding batch (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Failed to embed batch after {max_retries} attempts. Response: {getattr(e, 'response', 'N/A')}")
                    raise
                import time
                time.sleep(2.0)
        
        # Sleep slightly between batches to avoid rate limits
        if i + batch_size < len(texts):
            import time
            time.sleep(1.0)
            
    return all_embeddings

def embed_query(client: genai.Client, query: str) -> List[float]:
    """
    Embeds a single query string for retrieval.
    
    Args:
        client (genai.Client): The initialized Gemini client.
        query (str): The query text to embed.
        
    Returns:
        List[float]: A single embedding vector.
    """
    response = client.models.embed_content(
        model=config.EMBEDDING_MODEL,
        contents=[query],
        config=types.EmbedContentConfig(
            task_type='RETRIEVAL_QUERY',
            output_dimensionality=config.EMBEDDING_DIMENSIONS
        )
    )
    
    if hasattr(response, 'embeddings'):
        return response.embeddings[0].values
    else:
        return response[0].values
