from django.conf import settings
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from minio import Minio
from minio.error import S3Error
from io import BytesIO
import os
from urllib.parse import urljoin
from wallet.models.wallet import Wallet
from typing import Union


def get_minio_client():
    """Get configured MinIO client"""
    try:
        if not getattr(settings, 'USE_MINIO', False):
            return None
            
        client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL
        )
        return client
    except Exception as e:
        print(f"Error creating MinIO client: {e}")
        return None


def upload_to_minio(client, bucket_name, object_name, data, length, content_type='application/octet-stream'):
    """Upload data to MinIO"""
    try:
        client.put_object(
            bucket_name,
            object_name,
            data,
            length,
            content_type=content_type
        )
        return True
    except S3Error as e:
        print(f"Error uploading to MinIO: {e}")
        return False


def delete_from_minio(client, bucket_name, object_name):
    """Delete object from MinIO"""
    try:
        client.remove_object(bucket_name, object_name)
        return True
    except S3Error as e:
        print(f"Error deleting from MinIO: {e}")
        return False


def download_from_minio(client, bucket_name, object_name):
    """Download object from MinIO"""
    try:
        response = client.get_object(bucket_name, object_name)
        data = response.read()
        response.close()
        response.release_conn()
        return data
    except S3Error as e:
        print(f"Error downloading from MinIO: {e}")
        return None


def get_user_balance(user_pk: int) -> Union[int, list]:
    user_wallets = Wallet.objects.filter(owner=user_pk)
    wallet_values = []
    user_balance = 0

    for wallet in user_wallets:
        value = wallet.quantity * wallet.token.actual_price
        user_balance += value
        wallet_values.append(round(value, 2))

    return round(user_balance, 2), wallet_values, user_wallets


class MinIOStorage(Storage):
    """Custom Django storage backend for MinIO"""
    
    def __init__(self):
        self.client = get_minio_client()
        self.bucket_name = getattr(settings, 'MINIO_BUCKET_NAME', 'crypto-exchange')
        self.base_url = getattr(settings, 'MEDIA_URL', '')
        
    def _open(self, name, mode='rb'):
        """Open file from MinIO"""
        if not self.client:
            raise Exception("MinIO client not available")
            
        try:
            data = download_from_minio(self.client, self.bucket_name, name)
            if data:
                return ContentFile(data)
            else:
                raise FileNotFoundError(f"File {name} not found in MinIO")
        except Exception as e:
            raise Exception(f"Error opening file {name}: {e}")
    
    def _save(self, name, content):
        """Save file to MinIO"""
        if not self.client:
            raise Exception("MinIO client not available")
            
        try:
            # Ensure bucket exists
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
            
            # Get content type
            content_type = getattr(content, 'content_type', 'application/octet-stream')
            
            # Read content
            if hasattr(content, 'read'):
                data = content.read()
                if hasattr(content, 'seek'):
                    content.seek(0)  # Reset file pointer
            else:
                data = content
                
            # Upload to MinIO
            data_stream = BytesIO(data)
            success = upload_to_minio(
                self.client,
                self.bucket_name,
                name,
                data_stream,
                len(data),
                content_type
            )
            
            if success:
                return name
            else:
                raise Exception(f"Failed to upload {name} to MinIO")
                
        except Exception as e:
            raise Exception(f"Error saving file {name}: {e}")
    
    def delete(self, name):
        """Delete file from MinIO"""
        if not self.client:
            return False
            
        return delete_from_minio(self.client, self.bucket_name, name)
    
    def exists(self, name):
        """Check if file exists in MinIO"""
        if not self.client:
            return False
            
        try:
            self.client.stat_object(self.bucket_name, name)
            return True
        except S3Error:
            return False
    
    def size(self, name):
        """Get file size from MinIO"""
        if not self.client:
            return 0
            
        try:
            stat = self.client.stat_object(self.bucket_name, name)
            return stat.size
        except S3Error:
            return 0
    
    def url(self, name):
        """Get URL for file in MinIO"""
        if name:
            return urljoin(self.base_url, name)
        return None
    
    def get_available_name(self, name, max_length=None):
        """Get available filename"""
        # MinIO can overwrite files, so we can use the original name
        return name
