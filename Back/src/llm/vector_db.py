import chromadb
import json
import logging
from typing import List, Dict, Optional
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

class LoanVectorDB:
    def __init__(self, db_path: str = "loans_vector.db"):
        try:
            self.client = chromadb.PersistentClient(path=db_path)
            self.embedding_function = embedding_functions.OllamaEmbeddingFunction(
                model_name="nomic-embed-text"
            )
            self.collection = self.client.get_or_create_collection(
                name="loan_assessments",
                metadata={"hnsw:space": "cosine"},
                embedding_function=self.embedding_function
            )
            logger.info(f"Vector DB initialized at {db_path}")
        except Exception as e:
            logger.error(f"Vector DB initialization failed: {str(e)}")
            raise

    def store_loan(
        self, 
        loan_data: Dict,
        embedding: List[float],
        metadata: Optional[Dict] = None
    ) -> bool:
        try:
            loan_id = str(loan_data.get('loan_info', {}).get('basic_info', {}).get('loan_id', 'unknown'))
            
            self.collection.upsert(
                ids=[f"loan_{loan_id}"],
                embeddings=[embedding],
                documents=[json.dumps(loan_data)],
                metadatas=[{
                    'loan_id': loan_id,
                    'has_feedback': False,
                    **(metadata or {})
                }]
            )
            logger.debug(f"Stored/updated loan {loan_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store loan: {str(e)}")
            return False

    def find_similar_loans(
        self, 
        query_embedding: List[float], 
        n_results: int = 3,
        min_similarity: float = 0.6
    ) -> Dict:
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            similarities = [
                1 - distance for distance in results['distances'][0]
            ] if results.get('distances') else []
            
            filtered_results = {
                'documents': [],
                'metadatas': [],
                'similarities': []
            }
            
            for doc, meta, sim in zip(
                results.get('documents', [[]])[0],
                results.get('metadatas', [[]])[0],
                similarities
            ):
                if sim >= min_similarity:
                    filtered_results['documents'].append(doc)
                    filtered_results['metadatas'].append(meta)
                    filtered_results['similarities'].append(sim)
            
            logger.info(
                f"Found {len(filtered_results['documents'])} similar loans "
                f"(min similarity: {min_similarity})"
            )
            return filtered_results
            
        except Exception as e:
            logger.error(f"Vector DB query failed: {str(e)}")
            return {
                'documents': [],
                'metadatas': [],
                'similarities': []
            }

    def get_loan_count(self) -> int:
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Failed to get loan count: {str(e)}")
            return 0