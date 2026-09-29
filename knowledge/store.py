import os
from typing import List, Dict, Any, Optional

import lancedb

import config

class KnowledgeStore:
    """
    LanceDB vector store management for the Research Synthesizer.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initializes the KnowledgeStore and connects to LanceDB.
        
        Args:
            db_path (str, optional): Path to the LanceDB data directory. 
                                     Defaults to config.LANCEDB_PATH.
        """
        if db_path is None:
            db_path = config.LANCEDB_PATH
            
        # Ensure the directory exists
        os.makedirs(db_path, exist_ok=True)
        
        self.db_path = db_path
        self.db = lancedb.connect(db_path)
        
    def create_workspace(self, name: str, chunks: List[Dict[str, Any]], embeddings: List[List[float]]) -> int:
        """
        Creates a new LanceDB table named `name` or appends if it exists.
        
        Args:
            name (str): Name of the workspace/table.
            chunks (List[Dict[str, Any]]): List of chunk dictionaries. Each should have a 'metadata' dict and 'text' key.
            embeddings (List[List[float]]): List of embedding vectors corresponding to the chunks.
            
        Returns:
            int: Number of chunks stored.
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks and embeddings must match.")
            
        data = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            metadata = chunk.get('metadata', {})
            
            record = {
                'id': f"{name}_{i}",
                'text': chunk.get('text', ''),
                'vector': embedding,
                'source_url': metadata.get('source_url', ''),
                'page': metadata.get('page', 0),
                'doc_title': metadata.get('doc_title', ''),
                'chunk_index': metadata.get('chunk_index', i)
            }
            data.append(record)
            
        tables = self.db.table_names()
        if name in tables:
            table = self.db.open_table(name)
            table.add(data)
        else:
            self.db.create_table(name, data)
            
        return len(data)

    def search(self, workspace: str, query_vector: List[float], top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Runs a vector search on the specified workspace table.
        
        Args:
            workspace (str): Name of the workspace/table to search.
            query_vector (List[float]): The embedding vector of the query.
            top_k (int, optional): Number of top results to return. Defaults to config.DEFAULT_TOP_K.
            
        Returns:
            List[Dict[str, Any]]: List of matching records as dictionaries.
        """
        if top_k is None:
            top_k = config.DEFAULT_TOP_K
            
        try:
            table = self.db.open_table(workspace)
        except Exception as e:
            raise ValueError(f"Workspace '{workspace}' not found or could not be opened: {e}")
            
        results = table.search(query_vector).limit(top_k).to_list()
        return results

    def list_workspaces(self) -> List[str]:
        """
        Lists all available workspaces (tables).
        
        Returns:
            List[str]: List of workspace names.
        """
        return self.db.table_names()

    def delete_workspace(self, name: str) -> bool:
        """
        Deletes the specified workspace (drops the table).
        
        Args:
            name (str): Name of the workspace to delete.
            
        Returns:
            bool: True if successfully deleted, False otherwise.
        """
        try:
            self.db.drop_table(name)
            return True
        except Exception:
            return False

    def get_workspace_stats(self, name: str) -> Dict[str, int]:
        """
        Returns statistics about the specified workspace.
        
        Args:
            name (str): Name of the workspace.
            
        Returns:
            Dict[str, int]: Statistics dictionary with 'chunk_count' and 'doc_count'.
        """
        try:
            table = self.db.open_table(name)
            df = table.to_pandas()
            
            chunk_count = len(df)
            doc_count = df['source_url'].nunique() if 'source_url' in df.columns else 0
            
            return {
                'chunk_count': chunk_count,
                'doc_count': doc_count
            }
        except Exception as e:
            raise ValueError(f"Could not retrieve stats for workspace '{name}': {e}")
