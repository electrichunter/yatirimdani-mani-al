"""
Vector Store Management
Handles ChromaDB for strategy document embeddings
"""

import os
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import config
from utils.logger import setup_logger

logger = setup_logger("VectorStore")


class VectorStore:
    """Manages ChromaDB vector database for strategy documents"""
    
    def __init__(self, persist_directory=None, embedding_model=None):
        """
        Args:
            persist_directory: Where to store ChromaDB data
            embedding_model: Model name for embeddings
        """
        self.persist_directory = persist_directory or config.VECTOR_DB_PATH
        self.embedding_model_name = embedding_model or config.EMBEDDING_MODEL
        
        # Create directory if needed
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model
        logger.info(f"🔧 Loading embedding model: {self.embedding_model_name}")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        logger.info(f"✅ Embedding model loaded")
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="trading_strategies",
            metadata={"description": "Trading strategy knowledge base"}
        )
        
        logger.info(f"✅ Vector store initialized ({self.collection.count()} documents)")
    
    def add_text(self, text, doc_id, metadata=None):
        """
        Add text to vector store
        
        Args:
            text: Text content to embed
            doc_id: Unique document ID
            metadata: Optional metadata dict
        """
        # Generate embedding
        embedding = self.embedding_model.encode(text).tolist()
        
        # Add to collection
        self.collection.add(
            embeddings=[embedding],
            documents=[text],
            ids=[doc_id],
            metadatas=[metadata] if metadata else None
        )
    
    def add_texts(self, texts, doc_ids, metadatas=None):
        """
        Add multiple texts in batch
        
        Args:
            texts: List of text content
            doc_ids: List of unique IDs
            metadatas: Optional list of metadata dicts
        """
        # Generate embeddings in batch
        embeddings = self.embedding_model.encode(texts).tolist()
        
        # Add to collection
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            ids=doc_ids,
            metadatas=metadatas
        )
        
        logger.info(f"✅ Added {len(texts)} documents to vector store")
    
    def query(self, query_text, top_k=None):
        """
        Search for similar documents
        
        Args:
            query_text: Query string
            top_k: Number of results to return (default from config)
            
        Returns:
            List of relevant text excerpts
        """
        if top_k is None:
            top_k = config.RAG_TOP_K
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query_text).tolist()
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Extract documents
        if results and results.get("documents"):
            return results["documents"][0]  # First query results
        
        return []
    
    def count(self):
        """Get number of documents in store"""
        return self.collection.count()
    
    def clear(self):
        """Delete all documents"""
        self.client.delete_collection("trading_strategies")
        self.collection = self.client.create_collection("trading_strategies")
        logger.info("🗑️ Vector store cleared")
