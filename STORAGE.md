# Storage Configuration for Crypto Exchange

This guide explains how to configure file storage for your Django Crypto Exchange application with support for both local storage and MinIO object storage using the official MinIO Python client.

## Storage Options

### 1. Local Storage (Default)
- Files stored in `media/` directory
- Good for development and single-server deployments
- **Not suitable for horizontal scaling**

### 2. MinIO Object Storage
- S3-compatible object storage with direct MinIO client
- Perfect for production and scaling
- **Enables stateless, horizontally scalable architecture**

## Quick Start

### Option A: Local Storage (Default)
No additional setup required. Files will be stored in the `media/` directory.

```bash
# Just run your application
python manage.py runserver
```

### Option B: MinIO Storage

1. **Start MinIO server:**
```bash
# Using Docker Compose
docker-compose -f docker-compose.storage.yml up -d minio

# Or install MinIO locally
# Download from: https://min.io/download
```

2. **Configure environment variables:**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file and set:
USE_MINIO=true
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=crypto-exchange
```

3. **Install dependencies:**
```bash
pip install minio
```

4. **Setup MinIO bucket:**
```bash
python scripts/setup_minio.py
```

5. **Run migrations (if needed):**
```bash
python manage.py makemigrations
python manage.py migrate
```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `USE_MINIO` | Enable MinIO storage | `false` | No |
| `MINIO_ENDPOINT` | MinIO server endpoint | `localhost:9000` | Yes (if USE_MINIO=true) |
| `MINIO_ACCESS_KEY` | MinIO access key | `minioadmin` | Yes (if USE_MINIO=true) |
| `MINIO_SECRET_KEY` | MinIO secret key | `minioadmin` | Yes (if USE_MINIO=true) |
| `MINIO_BUCKET_NAME` | Bucket name | `crypto-exchange` | No |
| `MINIO_USE_SSL` | Use HTTPS | `false` | No |

## MinIO Web Console

Access MinIO web console at: http://localhost:9001
- Username: `minioadmin`
- Password: `minioadmin`

## Architecture

### MinIO Client Integration
The application uses the official **MinIO Python client** for direct object storage operations:

```python
from minio import Minio

# Create client
client = Minio(
    'localhost:9000',
    access_key='minioadmin',
    secret_key='minioadmin',
    secure=False
)

# Upload file
client.put_object('bucket', 'object-name', data, length)

# Download file  
response = client.get_object('bucket', 'object-name')
data = response.read()
```

### Custom Storage Backend
- **MinIOStorage**: Custom Django storage backend for seamless integration
- **Automatic bucket creation**: Sets up MinIO bucket if it doesn't exist
- **Error handling**: Graceful fallbacks to prevent application crashes

## Image Processing

Both storage options support automatic image resizing:
- **Profile images**: Resized to 300x300px
- **Token logos**: Resized to 200x200px
- **Quality**: 85% JPEG/PNG optimization
- **MinIO processing**: Images downloaded, processed, and re-uploaded

## Production Deployment

### With MinIO:
```bash
# Set environment variables
export USE_MINIO=true
export MINIO_ENDPOINT=your-minio-server.com:9000
export MINIO_ACCESS_KEY=your_production_key
export MINIO_SECRET_KEY=your_production_secret
export MINIO_USE_SSL=true

# Deploy multiple app instances
docker run -d --name crypto-app-1 -p 8001:8000 crypto-exchange
docker run -d --name crypto-app-2 -p 8002:8000 crypto-exchange
docker run -d --name crypto-app-3 -p 8003:8000 crypto-exchange
```

### Load Balancer Configuration:
All instances can run simultaneously because files are stored in MinIO, not locally.

## Migration from Local to MinIO

1. **Backup current media files:**
```bash
tar -czf media_backup.tar.gz media/
```

2. **Setup MinIO and run setup script**

3. **Copy existing files to MinIO:**
```bash
# Use MinIO client (mc)
mc alias set local http://localhost:9000 minioadmin minioadmin
mc cp --recursive media/ local/crypto-exchange/
```

4. **Update environment and restart:**
```bash
export USE_MINIO=true
python manage.py runserver
```

## Troubleshooting

### Common Issues:

1. **MinIO connection failed:**
   - Check if MinIO server is running: `docker ps`
   - Verify endpoint and credentials in `.env`
   - Check firewall settings (ports 9000, 9001)

2. **Images not displaying:**
   - Verify MEDIA_URL configuration
   - Check MinIO bucket permissions
   - Ensure bucket exists: `python scripts/setup_minio.py`

3. **Upload errors:**
   - Check MinIO disk space
   - Verify write permissions
   - Check file size limits

### Verify Setup:
```bash
# Test MinIO connection
python scripts/setup_minio.py

# Check current storage backend
python manage.py shell
>>> from django.conf import settings
>>> print(f"MinIO enabled: {settings.USE_MINIO}")
>>> print(f"Endpoint: {getattr(settings, 'MINIO_ENDPOINT', 'Not set')}")
```

## Benefits of MinIO Client

✅ **Direct Control**: Full access to MinIO-specific features  
✅ **Performance**: Optimized for object storage operations  
✅ **Simplicity**: No S3 abstraction layer overhead  
✅ **Error Handling**: Specific MinIO error types  
✅ **Feature Rich**: Access to all MinIO capabilities  

## File Operations

### Upload Process:
1. Django receives file upload
2. Custom storage backend processes file
3. MinIO client uploads to bucket
4. URL generated for access

### Download Process:
1. Request for file URL
2. MinIO serves file directly
3. Or proxied through Django if needed

## File Structure

```
media/
├── profile_pics/
│   ├── user1_avatar.jpg
│   └── user2_avatar.png
├── token_logo/
│   ├── bitcoin_icon.png
│   └── ethereum_icon.png
└── default_avatar.jpg
```

Same structure is maintained in MinIO bucket as object keys.