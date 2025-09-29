import os
import sys
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(project_dir))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Exchange.settings')

import django
django.setup()

from django.conf import settings
from minio import Minio
from minio.error import S3Error
from io import BytesIO

def setup_minio_bucket():
    """Create MinIO bucket if it doesn't exist"""
    if not getattr(settings, 'USE_MINIO', False):
        print("MinIO is not enabled. Set USE_MINIO=true in your environment.")
        return False
    
    try:
        # Create MinIO client
        client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL
        )
        
        bucket_name = settings.MINIO_BUCKET_NAME
        
        # Check if bucket exists
        try:
            if client.bucket_exists(bucket_name):
                print(f"✅ Bucket '{bucket_name}' already exists")
            else:
                # Bucket doesn't exist, create it
                client.make_bucket(bucket_name)
                print(f"✅ Successfully created bucket '{bucket_name}'")
                
        except S3Error as e:
            print(f"❌ Error with bucket operations: {e}")
            return False
        
        # Test upload/download
        test_key = 'test-connection.txt'
        test_content = b'MinIO connection test'
        
        try:
            # Upload test file
            client.put_object(
                bucket_name,
                test_key,
                BytesIO(test_content),
                len(test_content),
                content_type='text/plain'
            )
            print("✅ Successfully uploaded test file")
            
            # Download test file
            response = client.get_object(bucket_name, test_key)
            downloaded_data = response.read()
            response.close()
            response.release_conn()
            
            if downloaded_data == test_content:
                print("✅ Successfully downloaded test file")
            
            # Clean up test file
            client.remove_object(bucket_name, test_key)
            print("✅ MinIO setup complete!")
            return True
            
        except S3Error as e:
            print(f"❌ Error testing MinIO connection: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up MinIO: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Setting up MinIO for Crypto Exchange...")
    print(f"Endpoint: {getattr(settings, 'MINIO_ENDPOINT', 'Not configured')}")
    print(f"Bucket: {getattr(settings, 'MINIO_BUCKET_NAME', 'Not configured')}")
    print("=" * 50)
    
    success = setup_minio_bucket()
    if success:
        print("\n✅ MinIO setup completed successfully!")
        print("You can now upload images and they will be stored in MinIO.")
    else:
        print("\n❌ MinIO setup failed. Please check your configuration.")
        sys.exit(1)