import chromadb
import logging
from chromadb.utils import embedding_functions

def migrate_db():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        client = chromadb.PersistentClient(path="loans_vector.db")
        
        # Delete old collection if exists
        try:
            client.delete_collection("loan_assessments")
            logger.info("Deleted old collection")
        except Exception as e:
            logger.info("No existing collection to delete")
        
        # Create new collection with correct embedding function
        embedding_func = embedding_functions.OllamaEmbeddingFunction(
            model_name="nomic-embed-text"  # Removed api_base parameter
        )
        
        collection = client.get_or_create_collection(
            name="loan_assessments",
            metadata={"hnsw:space": "cosine"},
            embedding_function=embedding_func
        )
        
        logger.info("Successfully created new collection with proper dimensions")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    migrate_db()