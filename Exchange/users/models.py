from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from django.conf import settings
from django.core.files.base import ContentFile
from io import BytesIO
import os


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default_avatar.jpg', upload_to='profile_pics')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._resize_image()

    def _resize_image(self):
        """Resize image to 300x300 pixels - works with both local and MinIO storage"""
        if not self.image or self.image.name == 'default_avatar.jpg':
            return
            
        try:
            # Check if using MinIO or local storage
            use_minio = getattr(settings, 'USE_MINIO', False)
            
            if use_minio:
                # MinIO storage - use MinIO client
                from .utils import get_minio_client, upload_to_minio, delete_from_minio
                
                minio_client = get_minio_client()
                if not minio_client:
                    return
                
                bucket_name = settings.MINIO_BUCKET_NAME
                object_name = self.image.name
                
                try:
                    # Download image from MinIO
                    response = minio_client.get_object(bucket_name, object_name)
                    img_data = response.read()
                    img = Image.open(BytesIO(img_data))
                    
                    if img.height > 300 or img.width > 300:
                        output_size = (300, 300)
                        img.thumbnail(output_size, Image.Resampling.LANCZOS)
                        
                        # Save resized image to buffer
                        img_buffer = BytesIO()
                        img_format = img.format or 'JPEG'
                        img.save(img_buffer, format=img_format, quality=85, optimize=True)
                        img_buffer.seek(0)
                        
                        # Upload resized image back to MinIO
                        upload_to_minio(
                            minio_client,
                            bucket_name,
                            object_name,
                            img_buffer,
                            len(img_buffer.getvalue()),
                            content_type=f'image/{img_format.lower()}'
                        )
                        
                except Exception as e:
                    print(f"Error processing MinIO image: {e}")
                finally:
                    if 'response' in locals():
                        response.close()
                        response.release_conn()
            else:
                # Local storage - work with file path
                if hasattr(self.image, 'path') and self.image.path:
                    img = Image.open(self.image.path)
                    
                    if img.height > 300 or img.width > 300:
                        output_size = (300, 300)
                        img.thumbnail(output_size, Image.Resampling.LANCZOS)
                        img.save(self.image.path, quality=85, optimize=True)
                        
        except Exception as e:
            # Log error but don't prevent saving
            print(f"Error resizing profile image: {e}")

    def __str__(self):
        return f"Profile of {self.user.username}"
