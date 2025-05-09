import io
import logging
from typing import Optional

import aioboto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.security import encrypt_file, decrypt_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a session and client for MinIO
session = aioboto3.Session(
    aws_access_key_id=settings.MINIO_ACCESS_KEY,
    aws_secret_access_key=settings.MINIO_SECRET_KEY,
)

async def init_minio():
    """
    Initialize MinIO connection and create bucket if it doesn't exist.
    """
    print(settings.MINIO_ENDPOINT)
    async with session.client(
        's3',
        endpoint_url=f"{'https' if settings.MINIO_SECURE else 'http'}://{settings.MINIO_ENDPOINT}",
    ) as s3:
        try:
            # Check if bucket exists
            await s3.head_bucket(Bucket=settings.MINIO_BUCKET_NAME)
        except ClientError as e:
            # If bucket doesn't exist, create it
            if e.response['Error']['Code'] == '404':
                await s3.create_bucket(Bucket=settings.MINIO_BUCKET_NAME)
                logger.info(f"Created MinIO bucket: {settings.MINIO_BUCKET_NAME}")
            else:
                logger.error(f"Error connecting to MinIO: {str(e)}")
                raise

async def upload_file(file_content: bytes, file_path: str) -> tuple[str, bytes, str]:
    """
    Upload a file to MinIO with encryption.
    Returns (object_path, nonce, file_hash)
    """
    # Encrypt file content
    encrypted_content, nonce = encrypt_file(file_content)
    
    # Calculate SHA-256 hash of original content
    import hashlib
    file_hash = hashlib.sha256(file_content).hexdigest()
    
    # Upload to MinIO
    print(settings.MINIO_ENDPOINT)
    async with session.client(
        's3',
        endpoint_url=f"{'https' if settings.MINIO_SECURE else 'http'}://{settings.MINIO_ENDPOINT}",
    ) as s3:
        try:
            await s3.put_object(
                Bucket=settings.MINIO_BUCKET_NAME,
                Key=file_path,
                Body=encrypted_content
            )
            return file_path, nonce.hex(), file_hash
        except Exception as e:
            logger.error(f"Failed to upload file to MinIO: {str(e)}")
            raise

async def get_file(file_path: str, nonce_hex: str) -> Optional[bytes]:
    """
    Get a file from MinIO and decrypt it.
    """
    try:
        async with session.client(
            's3',
            endpoint_url=f"{'https' if settings.MINIO_SECURE else 'http'}://{settings.MINIO_ENDPOINT}",
        ) as s3:
            response = await s3.get_object(
                Bucket=settings.MINIO_BUCKET_NAME,
                Key=file_path
            )
            encrypted_content = await response['Body'].read()

            # Convert hex nonce back to bytes
            nonce = bytes.fromhex(nonce_hex)

            # Decrypt content
            decrypted_content = decrypt_file(encrypted_content, nonce)
            return decrypted_content
    except Exception as e:
        logger.error(f"Failed to get file from MinIO: {str(e)}")
        return None

async def get_document_file(document_id: int, version_id: int) -> io.BytesIO:
    """
    Get a document file by document_id and version_id.
    Returns a file-like object for streaming.
    """
    from app.db.session import SessionLocal
    from app.crud.crud_document import document_crud
    
    async with SessionLocal() as db:
        version = await document_crud.get_version(db, version_id=version_id)
        if not version:
            raise ValueError(f"Document version {version_id} not found")
        
        file_content = await get_file(version.storage_path, version.nonce)
        if not file_content:
            raise ValueError(f"Failed to retrieve file content for document {document_id}")
        
        return io.BytesIO(file_content)

async def delete_file(file_path: str) -> bool:
    """
    Delete a file from MinIO.
    """
    try:
        async with session.client(
            's3',
            endpoint_url=f"{'https' if settings.MINIO_SECURE else 'http'}://{settings.MINIO_ENDPOINT}",
        ) as s3:
            await s3.delete_object(
                Bucket=settings.MINIO_BUCKET_NAME,
                Key=file_path
            )
            return True
    except Exception as e:
        logger.error(f"Failed to delete file from MinIO: {str(e)}")
        return False
