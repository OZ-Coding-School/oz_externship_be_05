import logging
import uuid
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from mypy_boto3_s3 import S3Client as BotoS3Client

logger = logging.getLogger(__name__)


class S3Client:
    def __init__(self) -> None:
        aws_access_key_id = getattr(settings, "AWS_S3_ACCESS_KEY_ID", None)
        aws_secret_access_key = getattr(settings, "AWS_S3_SECRET_ACCESS_KEY", None)
        aws_region = getattr(settings, "AWS_S3_REGION", "ap-northeast-2")
        self.bucket_name = getattr(settings, "AWS_S3_BUCKET_NAME", "my-bucket")

        self.s3: BotoS3Client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region,
        )

    def upload(self, file: Any, path_prefix: str = "", extra_args: Optional[Dict[str, Any]] = None) -> str:
        original_name = getattr(file, "name", "unknown_file")
        ext = original_name.split(".")[-1] if "." in original_name else "bin"

        file_name = f"{uuid.uuid4()}.{ext}"

        clean_prefix = path_prefix.rstrip("/")
        key = f"{clean_prefix}/{file_name}" if clean_prefix else file_name
        key = key.lstrip("/")

        upload_params: Dict[str, Any] = extra_args.copy() if extra_args else {}

        if "ContentType" not in upload_params:
            content_type = getattr(file, "content_type", None)
            if content_type:
                upload_params["ContentType"] = content_type

        try:
            self.s3.upload_fileobj(file, self.bucket_name, key, ExtraArgs=upload_params)
            return key
        except ClientError as e:
            logger.error(f"S3 Upload Error: {e}", exc_info=True)
            raise e

    def upload_with_key(self, file: Any, key: str, extra_args: Optional[Dict[str, Any]] = None) -> str:
        clean_key = key.lstrip("/")
        upload_params: Dict[str, Any] = extra_args.copy() if extra_args else {}

        if "ContentType" not in upload_params:
            content_type = getattr(file, "content_type", None)
            if content_type:
                upload_params["ContentType"] = content_type

        try:
            self.s3.upload_fileobj(file, self.bucket_name, clean_key, ExtraArgs=upload_params)
            return clean_key
        except ClientError as e:
            logger.error(f"S3 Upload Error: {e}", exc_info=True)
            raise e

    def delete(self, key: str) -> None:
        if not key:
            return
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=key)
        except ClientError as e:
            logger.warning(f"S3 Delete Failed (Key: {key}): {e}", exc_info=True)

    def delete_prefix(self, prefix: str) -> None:
        """특정 경로(prefix)로 시작하는 모든 객체를 삭제"""
        objects_to_delete = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)

        if "Contents" in objects_to_delete:
            delete_keys: Any = [{"Key": obj["Key"]} for obj in objects_to_delete["Contents"]]
            self.s3.delete_objects(Bucket=self.bucket_name, Delete={"Objects": delete_keys})

    def build_url(self, key: str) -> str:
        if not key:
            return ""

        custom_domain = getattr(settings, "AWS_S3_CUSTOM_DOMAIN", None)

        if custom_domain:
            domain = custom_domain
        else:
            region = getattr(settings, "AWS_S3_REGION", "ap-northeast-2")
            domain = f"{self.bucket_name}.s3.{region}.amazonaws.com"

        return f"https://{domain.rstrip('/')}/{key.lstrip('/')}"

    def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        try:
            url = self.s3.generate_presigned_url(
                ClientMethod="put_object", Params={"Bucket": self.bucket_name, "Key": key}, ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL (Key: {key}): {e}", exc_info=True)
            raise e
