"""
test_all_connections.py
Comprehensive database connection test for all 4 databases
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from config.connections import db

def test_all_connections():
    """Test MySQL, MongoDB, Redis, and Cloudinary connections"""
    
    print("\n" + "="*60)
    print("🔌 TESTING ALL DATABASE CONNECTIONS")
    print("="*60)
    
    results = {}
    
    # ==================== MYSQL ====================
    print("\n📊 MySQL:")
    try:
        mysql_ok = db.setup_mysql()
        if mysql_ok:
            conn = db.get_mysql_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT VERSION() as version, DATABASE() as db')
            data = cursor.fetchone()
            print(f"   ✅ Connected!")
            print(f"      Version: {data['version']}")
            print(f"      Database: {data['db']}")
            cursor.close()
            conn.close()
            results['mysql'] = True
        else:
            print("   ❌ Connection failed")
            results['mysql'] = False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results['mysql'] = False
    
    # ==================== MONGODB ====================
    print("\n📊 MongoDB:")
    try:
        mongo_ok = db.setup_mongodb()
        if mongo_ok:
            mongo_db = db.get_mongodb()
            collections = mongo_db.list_collection_names()
            print(f"   ✅ Connected!")
            print(f"      Database: {mongo_db.name}")
            print(f"      Collections: {collections}")
            
            if 'face_embeddings' in collections:
                count = mongo_db.face_embeddings.count_documents({})
                print(f"      Face embeddings: {count} documents")
            
            results['mongodb'] = True
        else:
            print("   ❌ Connection failed")
            results['mongodb'] = False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results['mongodb'] = False
    
    # ==================== REDIS ====================
    print("\n📊 Redis:")
    try:
        redis_ok = db.setup_redis()
        if redis_ok:
            redis_client = db.get_redis()
            test_key = "test:connection:check"
            redis_client.setex(test_key, 10, "working")
            value = redis_client.get(test_key)
            info = redis_client.info()
            
            print(f"   ✅ Connected!")
            print(f"      Test value: {value}")
            print(f"      Redis Version: {info.get('redis_version', 'unknown')}")
            
            redis_client.delete(test_key)
            results['redis'] = True
        else:
            print("   ❌ Connection failed")
            results['redis'] = False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results['redis'] = False
    
    # ==================== CLOUDINARY ====================
    print("\n📊 Cloudinary:")
    try:
        import cloudinary
        import cloudinary.api
        
        cloud_ok = db.setup_cloudinary()
        if cloud_ok:
            usage = cloudinary.api.usage()
            print(f"   ✅ Connected!")
            print(f"      Cloud Name: {cloudinary.config().cloud_name}")
            print(f"      Plan: {usage.get('plan', 'Free')}")
            results['cloudinary'] = True
        else:
            print("   ❌ Connection failed")
            results['cloudinary'] = False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results['cloudinary'] = False
    
    # ==================== SUMMARY ====================
    print("\n" + "="*60)
    print("📋 CONNECTION SUMMARY")
    print("="*60)
    
    all_connected = True
    for name, status in results.items():
        icon = "✅" if status else "❌"
        print(f"   {icon} {name.upper():12} : {'CONNECTED' if status else 'FAILED'}")
        if not status:
            all_connected = False
    
    print("="*60)
    
    if all_connected:
        print("\n🎉 ALL DATABASES ARE CONNECTED AND READY!")
    else:
        print("\n⚠️  SOME CONNECTIONS FAILED!")
    
    print("="*60 + "\n")
    
    return results

if __name__ == "__main__":
    test_all_connections()