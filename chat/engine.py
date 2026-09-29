import logging
from typing import Any, Callable, Dict, Generator, List, Tuple

from google import genai
from google.genai import types

import config
from knowledge.embeddings import embed_query
from knowledge.store import KnowledgeStore

logger = logging.getLogger(__name__)


class ChatEngine:
    """
    RAG-powered chat engine.
    Retrieves relevant context and answers user queries using the generative model.
    """

    def __init__(self, client: genai.Client, store: KnowledgeStore):
        """
        Initialize the ChatEngine.

        Args:
            client: The initialized genai.Client
            store: The initialized KnowledgeStore to search for context
        """
        self.client = client
        self.store = store

    def _retrieve_context(self, workspace: str, question: str) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context chunks for a given question and workspace.

        Args:
            workspace: The workspace name to search in
            question: The user's question

        Returns:
            A list of dictionary chunks containing source context
        """
        try:
            query_vector = embed_query(self.client, question)
            # Assuming store.search(workspace, query_vector) returns top k matching chunks
            chunks = self.store.search(workspace, query_vector)
            return chunks
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []

    def _build_prompt(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        chat_history: List[Dict[str, str]] = None
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Build the messages list and system instructions for the generative model.

        Args:
            question: The user's question
            context_chunks: The retrieved chunks
            chat_history: The prior conversation turns

        Returns:
            A tuple of (contents list, system_instruction string)
        """
        # Format the context chunks as numbered sources
        if context_chunks:
            formatted_sources = []
            for i, chunk in enumerate(context_chunks, start=1):
                doc_title = chunk.get("doc_title", "Unknown Title")
                page = chunk.get("page", "N/A")
                source_url = chunk.get("source_url", "N/A")
                text = chunk.get("text", "")
                
                formatted_sources.append(
                    f"[{i}] Source: {doc_title} (Page {page}) | URL: {source_url}\n{text}\n---"
                )
            formatted_context = "\n".join(formatted_sources)
            system_instruction = config.RAG_SYSTEM_PROMPT.format(context=formatted_context)
        else:
            system_instruction = (
                "You are a precise research assistant. Answer the user's question using ONLY the provided source documents. "
                "However, no relevant source documents were found in the knowledge base for this query. "
                "You MUST inform the user that you don't have enough information in the loaded sources to answer the question."
            )

        contents = []
        if chat_history:
            for turn in chat_history:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                contents.append({"role": role, "parts": [{"text": content}]})

        contents.append({"role": "user", "parts": [{"text": question}]})

        return contents, system_instruction

    def ask(
        self,
        question: str,
        workspace: str,
        chat_history: List[Dict[str, str]] = None
    ) -> Tuple[Callable[[], Generator[str, None, None]], List[Dict[str, Any]]]:
        """
        Alias for ask_with_sources to fit the requested definition in some versions.
        Executes a full RAG pipeline and returns a stream generator and source chunks.
        """
        return self.ask_with_sources(question, workspace, chat_history)

    def ask_with_sources(
        self,
        question: str,
        workspace: str,
        chat_history: List[Dict[str, str]] = None
    ) -> Tuple[Callable[[], Generator[str, None, None]], List[Dict[str, Any]]]:
        """
        Execute the full RAG pipeline, retrieving sources and streaming the answer.

        Args:
            question: The user's question
            workspace: The workspace name to search in
            chat_history: The prior conversation turns

        Returns:
            A tuple containing:
            - stream_generator: A function that yields string chunks of the answer
            - source_chunks: A list of the retrieved chunks used for context
        """
        context_chunks = self._retrieve_context(workspace, question)
        contents, system_instruction = self._build_prompt(question, context_chunks, chat_history)

        def stream() -> Generator[str, None, None]:
            import time
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content_stream(
                        model=config.GENERATION_MODEL,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.3,
                        )
                    )
                    for chunk in response:
                        if chunk.text:
                            yield chunk.text
                    break # Success, exit retry loop
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        if attempt < max_retries - 1:
                            logger.warning(f"Rate limited during chat stream. Retrying in 20 seconds... (Attempt {attempt+1}/{max_retries})")
                            yield f"\n\n[Rate limit hit. Pausing for 20s before retry {attempt+1}/{max_retries}...]\n\n"
                            time.sleep(20)
                            continue
                    logger.error(f"Error generating content stream: {e}")
                    yield f"An error occurred while generating the response: {e}"
                    break

        return stream, context_chunks
