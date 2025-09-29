from django.db import models
from django.conf import settings
from PIL import Image
from io import BytesIO


class Token(models.Model):
    name = models.TextField(blank=False)
    symbol = models.TextField(max_length=10, blank=False)
    actual_price = models.FloatField(blank=False)
    image = models.ImageField(default='bitcoin_icon.png', upload_to='token_logo')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._resize_image()

    def _resize_image(self):
        """Resize token image - works with both local and MinIO storage"""
        if not self.image or 'bitcoin_icon' in self.image.name:
            return
            
        try:
            use_minio = getattr(settings, 'USE_MINIO', False)
            
            if use_minio:
                # MinIO storage - use MinIO client
                from users.utils import get_minio_client, upload_to_minio, download_from_minio
                
                minio_client = get_minio_client()
                if not minio_client:
                    return
                
                bucket_name = settings.MINIO_BUCKET_NAME
                object_name = self.image.name
                
                try:
                    # Download image from MinIO
                    img_data = download_from_minio(minio_client, bucket_name, object_name)
                    if not img_data:
                        return
                        
                    img = Image.open(BytesIO(img_data))
                    
                    if img.height > 200 or img.width > 200:
                        output_size = (200, 200)
                        img.thumbnail(output_size, Image.Resampling.LANCZOS)
                        
                        # Save resized image to buffer
                        img_buffer = BytesIO()
                        img_format = img.format or 'PNG'
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
                    print(f"Error processing MinIO token image: {e}")
            else:
                # Local storage
                if hasattr(self.image, 'path') and self.image.path:
                    img = Image.open(self.image.path)
                    
                    if img.height > 200 or img.width > 200:
                        output_size = (200, 200)
                        img.thumbnail(output_size, Image.Resampling.LANCZOS)
                        img.save(self.image.path, quality=85, optimize=True)
                        
        except Exception as e:
            print(f"Error resizing token image: {e}")

    def __str__(self):
        return f"{self.name}"
