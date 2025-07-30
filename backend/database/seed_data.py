"""
Database seeding script to initialize vector DB and embedding configurations from .env file
"""
import os
import logging
from typing import Dict, Any
from database.database import get_session
from database.models import VectorDBConfig, EmbeddingConfig
from config import Config

logger = logging.getLogger(__name__)

def get_vector_db_config_from_env() -> Dict[str, Any]:
    """Extract vector DB configuration from environment variables"""
    vector_db_type = Config.VECTOR_DB_TYPE.lower()
    
    if vector_db_type == 'pinecone':
        return {
            'api_key': Config.PINECONE_API_KEY,
            'index_name': Config.PINECONE_INDEX_NAME,
            'environment': Config.PINECONE_ENVIRONMENT,
            'dimension': Config.PINECONE_DIMENSION
        }
    elif vector_db_type == 'weaviate':
        return {
            'host': Config.WEAVIATE_HOST,
            'port': Config.WEAVIATE_PORT,
            'scheme': Config.WEAVIATE_SCHEME,
            'url': Config.WEAVIATE_URL,
            'api_key': Config.WEAVIATE_API_KEY,
            'class_name': Config.WEAVIATE_CLASS_NAME
        }
    elif vector_db_type == 'chroma':
        return {
            'path': Config.VECTOR_DB_PATH,
            'host': Config.CHROMA_HOST,
            'port': Config.CHROMA_PORT,
            'collection_name': Config.VECTOR_DB_COLLECTION
        }
    elif vector_db_type == 'qdrant':
        return {
            'host': Config.QDRANT_HOST,
            'port': Config.QDRANT_PORT,
            'api_key': Config.QDRANT_API_KEY,
            'collection_name': Config.QDRANT_COLLECTION,
            'vector_size': Config.QDRANT_VECTOR_SIZE
        }
    else:
        raise ValueError(f"Unsupported vector DB type: {vector_db_type}")

def get_embedding_config_from_env() -> Dict[str, Any]:
    """Extract embedding configuration from environment variables"""
    embedding_type = Config.EMBEDDING_MODEL_TYPE.lower()
    
    if embedding_type == 'openai':
        return {
            'api_key': Config.OPENAI_API_KEY,
            'model': Config.OPENAI_EMBEDDING_MODEL
        }
    elif embedding_type == 'anthropic':
        return {
            'api_key': Config.ANTHROPIC_API_KEY,
            'model': Config.ANTHROPIC_EMBEDDING_MODEL
        }
    elif embedding_type == 'huggingface':
        return {
            'model': Config.HUGGINGFACE_EMBEDDING_MODEL
        }
    elif embedding_type == 'deepseek':
        return {
            'api_key': Config.DEEPSEEK_API_KEY,
            'model': Config.DEEPSEEK_EMBEDDING_MODEL
        }
    else:
        raise ValueError(f"Unsupported embedding type: {embedding_type}")

def seed_vector_db_config():
    """Seed vector database configuration"""
    try:
        with get_session() as session:
            # Clear all existing configurations to force update
            existing_count = session.query(VectorDBConfig).count()
            if existing_count > 0:
                logger.info(f"Clearing {existing_count} existing vector DB configurations")
                session.query(VectorDBConfig).delete()
                session.commit()
            
            vector_db_type = Config.VECTOR_DB_TYPE.lower()
            vector_db_config = get_vector_db_config_from_env()
            
            # Create the configuration
            config = VectorDBConfig(
                name=f"default_{vector_db_type}",
                provider=vector_db_type,
                config=vector_db_config,
                is_default=True
            )
            
            session.add(config)
            session.commit()
            
            logger.info(f"✅ Successfully seeded vector DB configuration: {vector_db_type}")
            
    except Exception as e:
        logger.error(f"❌ Error seeding vector DB configuration: {e}")
        raise

def seed_embedding_config():
    """Seed embedding model configuration"""
    try:
        with get_session() as session:
            # Clear all existing configurations to force update
            existing_count = session.query(EmbeddingConfig).count()
            if existing_count > 0:
                logger.info(f"Clearing {existing_count} existing embedding configurations")
                session.query(EmbeddingConfig).delete()
                session.commit()
            
            embedding_type = Config.EMBEDDING_MODEL_TYPE.lower()
            embedding_config = get_embedding_config_from_env()
            model_name = embedding_config.get('model', 'default')
            
            # Create the configuration
            config = EmbeddingConfig(
                name=f"default_{embedding_type}",
                provider=embedding_type,
                model_name=model_name,
                config=embedding_config,
                is_default=True
            )
            
            session.add(config)
            session.commit()
            
            logger.info(f"✅ Successfully seeded embedding configuration: {embedding_type} ({model_name})")
            
    except Exception as e:
        logger.error(f"❌ Error seeding embedding configuration: {e}")
        raise

def seed_database():
    """Seed all configurations"""
    logger.info("🌱 Starting database seeding...")
    
    try:
        seed_vector_db_config()
        seed_embedding_config()
        logger.info("✅ Database seeding completed successfully")
    except Exception as e:
        logger.error(f"❌ Database seeding failed: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_database()