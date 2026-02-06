"""
Schema Storage Module
Stores schema information with embeddings for semantic search using SentenceTransformer.
"""

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
import pickle
import os
from pathlib import Path


class SchemaStore:
    """
    Stores schema information with embeddings for semantic column retrieval.
    Uses SentenceTransformer (all-MiniLM-L6-v2) for embedding generation.
    """
    
    def __init__(self, schema_df: pd.DataFrame, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the schema store.
        
        Args:
            schema_df: DataFrame with schema descriptions (Column_Name, Description, Example)
            model_name: Name of the SentenceTransformer model
        """
        self.schema_df = schema_df
        self.model = SentenceTransformer(model_name)
        self.column_embeddings = None
        self.column_info = {}
        self._build_schema_index()
    
    def _build_schema_index(self):
        """
        Build the schema index with embeddings for each column.
        """
        print("Building schema index with embeddings...")
        
        # Create a list of searchable texts for each column
        searchable_texts = []
        column_names = []
        
        for _, row in self.schema_df.iterrows():
            col_name = row['Column_Name'].strip().replace(' ', '_')
            description = str(row.get('Description', ''))
            example = str(row.get('Example', ''))
            
            # Create a rich searchable text combining name, description, and example
            searchable_text = f"{col_name}. {description}"
            if example and example != '-' and example != 'nan':
                searchable_text += f" Example: {example}"
            
            searchable_texts.append(searchable_text)
            column_names.append(col_name)
            
            # Store column info
            self.column_info[col_name] = {
                'description': description,
                'example': example,
                'original_name': row['Column_Name']
            }
        
        # Generate embeddings for all columns
        print(f"Generating embeddings for {len(searchable_texts)} columns...")
        self.column_embeddings = self.model.encode(searchable_texts, show_progress_bar=True)
        self.column_names = column_names
        
        print("Schema index built successfully!")
    
    def find_relevant_columns(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Find relevant columns based on semantic similarity to the query.
        
        Args:
            query: User query text
            top_k: Number of top columns to return
            
        Returns:
            List of dictionaries with column information
        """
        if self.column_embeddings is None:
            raise ValueError("Schema index not built. Call _build_schema_index() first.")
        
        # Encode the query
        query_embedding = self.model.encode([query])
        
        # Calculate cosine similarity
        similarities = np.dot(self.column_embeddings, query_embedding.T).flatten()
        
        # Get top_k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Build results
        results = []
        for idx in top_indices:
            col_name = self.column_names[idx]
            results.append({
                'column_name': col_name,
                'similarity': float(similarities[idx]),
                'description': self.column_info[col_name]['description'],
                'example': self.column_info[col_name]['example']
            })
        
        return results
    
    def get_column_info(self, column_name: str) -> Dict:
        """
        Get detailed information about a specific column.
        
        Args:
            column_name: Name of the column
            
        Returns:
            Dictionary with column information
        """
        return self.column_info.get(column_name, {})
    
    def save(self, filepath: str):
        """
        Save the schema store to disk.
        
        Args:
            filepath: Path to save the store
        """
        save_data = {
            'column_info': self.column_info,
            'column_names': self.column_names,
            'column_embeddings': self.column_embeddings,
            'schema_df': self.schema_df
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(save_data, f)
        
        print(f"Schema store saved to {filepath}")
    
    @classmethod
    def load(cls, filepath: str, model_name: str = "all-MiniLM-L6-v2"):
        """
        Load the schema store from disk.
        
        Args:
            filepath: Path to load the store from
            model_name: Name of the SentenceTransformer model (must match)
            
        Returns:
            SchemaStore instance
        """
        with open(filepath, 'rb') as f:
            save_data = pickle.load(f)
        
        store = cls.__new__(cls)
        store.model = SentenceTransformer(model_name)
        store.column_info = save_data['column_info']
        store.column_names = save_data['column_names']
        store.column_embeddings = save_data['column_embeddings']
        store.schema_df = save_data['schema_df']
        
        print(f"Schema store loaded from {filepath}")
        return store


if __name__ == "__main__":
    # Test the schema store
    from ingest import load_schema_description
    
    schema_df = load_schema_description()
    store = SchemaStore(schema_df)
    
    # Test queries
    test_queries = [
        "vision acuity",
        "diagnosis",
        "drug medication",
        "eye examination"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = store.find_relevant_columns(query, top_k=3)
        for result in results:
            print(f"  - {result['column_name']}: {result['similarity']:.3f}")
