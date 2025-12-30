from __future__ import annotations

import io
from typing import Any
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError
from django.test import TestCase, override_settings

from apps.core.utils.s3_client import S3Client


class DummyFile(io.BytesIO):
    def __init__(self, data: bytes, *, name: str, content_type: str) -> None:
        super().__init__(data)
        self.name = name
        self.content_type = content_type


class S3ClientTests(TestCase):
    def _make_client(self, mock_boto: MagicMock) -> tuple[S3Client, MagicMock]:
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        return S3Client(), mock_s3

    @override_settings(AWS_S3_BUCKET_NAME="bucket")
    @patch("apps.core.utils.s3_client.boto3.client")
    @patch("apps.core.utils.s3_client.uuid.uuid4", return_value="uuid")
    def test_upload_uses_uuid_and_content_type(self, _uuid: Any, mock_boto: MagicMock) -> None:
        client, mock_s3 = self._make_client(mock_boto)
        upload_file = DummyFile(b"data", name="photo.png", content_type="image/png")

        key = client.upload(upload_file, path_prefix="uploads")

        self.assertEqual(key, "uploads/uuid.png")
        mock_s3.upload_fileobj.assert_called_once()
        args, kwargs = mock_s3.upload_fileobj.call_args
        self.assertEqual(args[1], "bucket")
        self.assertEqual(args[2], "uploads/uuid.png")
        self.assertEqual(kwargs["ExtraArgs"]["ContentType"], "image/png")

    @override_settings(AWS_S3_BUCKET_NAME="bucket")
    @patch("apps.core.utils.s3_client.boto3.client")
    def test_upload_with_key_uses_fixed_key(self, mock_boto: MagicMock) -> None:
        client, mock_s3 = self._make_client(mock_boto)
        upload_file = io.BytesIO(b"data")

        key = client.upload_with_key(upload_file, key="/fixed/profile.png", extra_args={"ContentType": "image/png"})

        self.assertEqual(key, "fixed/profile.png")
        mock_s3.upload_fileobj.assert_called_once()
        args, kwargs = mock_s3.upload_fileobj.call_args
        self.assertEqual(args[2], "fixed/profile.png")
        self.assertEqual(kwargs["ExtraArgs"]["ContentType"], "image/png")

    @override_settings(AWS_S3_CUSTOM_DOMAIN="cdn.example.com")
    @patch("apps.core.utils.s3_client.boto3.client")
    def test_build_url_uses_custom_domain(self, mock_boto: MagicMock) -> None:
        client, _ = self._make_client(mock_boto)

        url = client.build_url("path/file.png")

        self.assertEqual(url, "https://cdn.example.com/path/file.png")

    @override_settings(AWS_S3_BUCKET_NAME="bucket", AWS_S3_REGION="ap-northeast-2")
    @patch("apps.core.utils.s3_client.boto3.client")
    def test_build_url_uses_region_domain(self, mock_boto: MagicMock) -> None:
        client, _ = self._make_client(mock_boto)

        url = client.build_url("path/file.png")

        self.assertEqual(url, "https://bucket.s3.ap-northeast-2.amazonaws.com/path/file.png")

    @override_settings(AWS_S3_BUCKET_NAME="bucket")
    @patch("apps.core.utils.s3_client.boto3.client")
    def test_generate_presigned_url(self, mock_boto: MagicMock) -> None:
        client, mock_s3 = self._make_client(mock_boto)
        mock_s3.generate_presigned_url.return_value = "signed"

        url = client.generate_presigned_url("path/file.png", expires_in=120)

        self.assertEqual(url, "signed")
        mock_s3.generate_presigned_url.assert_called_once_with(
            ClientMethod="put_object",
            Params={"Bucket": "bucket", "Key": "path/file.png"},
            ExpiresIn=120,
        )

    @override_settings(AWS_S3_BUCKET_NAME="bucket")
    @patch("apps.core.utils.s3_client.boto3.client")
    def test_delete_no_key_no_call(self, mock_boto: MagicMock) -> None:
        client, mock_s3 = self._make_client(mock_boto)

        client.delete("")

        mock_s3.delete_object.assert_not_called()

    @override_settings(AWS_S3_BUCKET_NAME="bucket")
    @patch("apps.core.utils.s3_client.boto3.client")
    def test_upload_raises_on_client_error(self, mock_boto: MagicMock) -> None:
        client, mock_s3 = self._make_client(mock_boto)
        mock_s3.upload_fileobj.side_effect = ClientError({"Error": {"Code": "403"}}, "Upload")
        upload_file = DummyFile(b"data", name="photo.png", content_type="image/png")

        with self.assertRaises(ClientError):
            client.upload(upload_file)
