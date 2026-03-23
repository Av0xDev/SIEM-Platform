"""
Database initialization and connection management
"""

from pymongo import MongoClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import logging

logger = logging.getLogger(__name__)

# Database URLs
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/siem_db')
POSTGRES_URL = os.getenv('DATABASE_URL', 'postgresql://siem_user:siem_password_123@localhost:5432/siem_db')

# MongoDB connection
mongo_client = None
db = None

def init_db():
    """Initialize database connections"""
    global mongo_client, db
    
    try:
        # MongoDB
        mongo_client = MongoClient(MONGODB_URL)
        db = mongo_client.siem_db
        
        # Test connection
        mongo_client.admin.command('ping')
        logger.info("Connected to MongoDB")
        
        # Create collections with indexes
        create_collections()
        
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise

def get_db():
    """Get database connection"""
    return db

def create_collections():
    """Create MongoDB collections with indexes"""
    if db is None:
        return
    
    # Logs collection
    if 'logs' not in db.list_collection_names():
        db.create_collection('logs')
        db.logs.create_index([('timestamp', -1)])
        db.logs.create_index([('source', 1)])
        db.logs.create_index([('level', 1)])
        db.logs.create_index([('ip_address', 1)])
    
    # Correlations collection
    if 'correlations' not in db.list_collection_names():
        db.create_collection('correlations')
        db.correlations.create_index([('timestamp', -1)])
        db.correlations.create_index([('severity', 1)])
    
    # Threat intelligence collection
    if 'threat_intel' not in db.list_collection_names():
        db.create_collection('threat_intel')
        db.threat_intel.create_index([('indicator', 1)])
        db.threat_intel.create_index([('type', 1)])
    
    # Audit logs collection
    if 'audit_logs' not in db.list_collection_names():
        db.create_collection('audit_logs')
        db.audit_logs.create_index([('timestamp', -1)])

def close_db():
    """Close database connections"""
    global mongo_client
    if mongo_client:
        mongo_client.close()