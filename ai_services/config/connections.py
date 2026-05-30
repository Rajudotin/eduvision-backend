"""
config/connections.py
Database connection pools for all 4 databases
"""

import os
from dotenv import load_dotenv
import pymysql
from pymysql.cursors import DictCursor
from pymongo import MongoClient
import redis
import cloudinary
import cloudinary.uploader
import cloudinary.api
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class DatabaseConnections:
    """Singleton class to manage all database connections"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.mysql_pool = None
        self.mongodb_client = None
        self.redis_client = None
        self.mongodb = None
        self._initialized = True
    
    # ==================== MYSQL CONNECTION ====================
    def setup_mysql(self):
        """Setup MySQL connection pool"""
        try:
            from dbutils.pooled_db import PooledDB
            
            self.mysql_pool = PooledDB(
                creator=pymysql,
                maxconnections=20,
                mincached=5,
                maxcached=10,
                blocking=True,
                host=os.getenv('MYSQL_HOST', 'localhost'),
                port=int(os.getenv('MYSQL_PORT', 3306)),
                user=os.getenv('MYSQL_USER', 'root'),
                password=os.getenv('MYSQL_PASSWORD', ''),
                database=os.getenv('MYSQL_DATABASE', 'eduvision'),
                charset='utf8mb4',
                cursorclass=DictCursor,
                autocommit=True
            )
            
            # Test connection
            conn = self.mysql_pool.connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            
            print("✅ MySQL Connected! Pool size: 5-20 connections")
            return True
            
        except Exception as e:
            print(f"❌ MySQL Connection Failed: {e}")
            return False
    
    def get_mysql_connection(self):
        """Get a connection from MySQL pool"""
        if self.mysql_pool:
            return self.mysql_pool.connection()
        return None
    
    # ==================== MONGODB CONNECTION ====================
    def setup_mongodb(self):
        """Setup MongoDB connection"""
        try:
            mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
            
            self.mongodb_client = MongoClient(
                mongodb_uri,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=60000,
                connectTimeoutMS=5000,
                serverSelectionTimeoutMS=5000
            )
            
            # Test connection
            self.mongodb_client.admin.command('ping')
            
            # Get database
            db_name = os.getenv('MONGODB_DB', 'eduvision')
            self.mongodb = self.mongodb_client[db_name]
            
            print(f"✅ MongoDB Connected! Database: {db_name}")
            return True
            
        except Exception as e:
            print(f"❌ MongoDB Connection Failed: {e}")
            return False
    
    def get_mongodb(self):
        """Get MongoDB database instance"""
        return self.mongodb if self.mongodb_client else None
    
    # ==================== REDIS CONNECTION ====================
    def setup_redis(self):
        """Setup Redis connection"""
        try:
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            redis_db = int(os.getenv('REDIS_DB', 0))
            
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            
            # Test connection
            response = self.redis_client.ping()
            
            if response:
                print(f"✅ Redis Connected! Host: {redis_host}:{redis_port}")
                return True
            else:
                print("❌ Redis Ping Failed")
                return False
                
        except Exception as e:
            print(f"❌ Redis Connection Failed: {e}")
            return False
    
    def get_redis(self):
        """Get Redis client"""
        return self.redis_client
    
    # ==================== CLOUDINARY SETUP ====================
    def setup_cloudinary(self):
        """Setup Cloudinary configuration"""
        try:
            cloudinary.config(
                cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
                api_key=os.getenv('CLOUDINARY_API_KEY'),
                api_secret=os.getenv('CLOUDINARY_API_SECRET'),
                secure=True
            )
            
            # Test connection
            result = cloudinary.api.usage()
            
            print(f"✅ Cloudinary Connected!")
            print(f"   Cloud: {os.getenv('CLOUDINARY_CLOUD_NAME')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Cloudinary Connection Failed: {e}")
            return False
    
    # ==================== SETUP ALL ====================
    def setup_all(self):
        """Setup all database connections"""
        print("\n" + "="*60)
        print("🔗 SETTING UP DATABASE CONNECTIONS")
        print("="*60)
        
        results = {
            'mysql': self.setup_mysql(),
            'mongodb': self.setup_mongodb(),
            'redis': self.setup_redis(),
            'cloudinary': self.setup_cloudinary()
        }
        
        print("\n" + "="*60)
        print("📊 CONNECTION SUMMARY")
        print("="*60)
        
        for db_name, status in results.items():
            icon = "✅" if status else "❌"
            print(f"{icon} {db_name.upper()}: {'Connected' if status else 'Failed'}")
        
        all_connected = all(results.values())
        
        if all_connected:
            print("\n🎉 ALL DATABASES CONNECTED SUCCESSFULLY!")
        else:
            print("\n⚠️ Some connections failed. Check errors above.")
        
        print("="*60)
        
        return results
    
    def health_check(self):
        """Check health of all connections"""
        health = {}
        
        # MySQL Health
        try:
            conn = self.get_mysql_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            health['mysql'] = 'healthy'
        except:
            health['mysql'] = 'unhealthy'
        
        # MongoDB Health
        try:
            if self.mongodb_client:
                self.mongodb_client.admin.command('ping')
                health['mongodb'] = 'healthy'
            else:
                health['mongodb'] = 'unhealthy'
        except:
            health['mongodb'] = 'unhealthy'
        
        # Redis Health
        try:
            if self.redis_client:
                self.redis_client.ping()
                health['redis'] = 'healthy'
            else:
                health['redis'] = 'unhealthy'
        except:
            health['redis'] = 'unhealthy'
        
        # Cloudinary Health
        try:
            cloudinary.api.usage()
            health['cloudinary'] = 'healthy'
        except:
            health['cloudinary'] = 'unhealthy'
        
        return health

# Global instance
db = DatabaseConnections()