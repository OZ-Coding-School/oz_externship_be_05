from __future__ import annotations

import io
from typing import Any

from PIL import Image, ImageOps
from rest_framework.exceptions import APIException

from apps.core.utils.s3_client import S3Client


class ImageResizer:
    def __init__(self, s3_client: S3Client | None = None) -> None:
        self.s3_client = s3_client or S3Client()

    def upload_square_resizes(
        self,
        *,
        image_file: Any,
        sizes: tuple[int, ...],
        path_prefix: str,
    ) -> dict[str, str]:
        urls: dict[str, str] = {}
        try:
            source = Image.open(image_file)
            source.load()
        except Exception as exc:
            raise APIException("이미지 처리에 실패했습니다.") from exc

        for size in sizes:
            try:
                resized = ImageOps.fit(
                    source,
                    (size, size),
                    method=Image.Resampling.LANCZOS,
                    centering=(0.5, 0.5),
                )
                buffer = io.BytesIO()
                buffer.name = f"image_{size}.png"
                resized.save(buffer, format="PNG")
                buffer.seek(0)
            except Exception as exc:
                raise APIException("이미지 처리에 실패했습니다.") from exc

            base_prefix = path_prefix.rstrip("/")
            key = self.s3_client.upload_with_key(
                buffer,
                key=f"{base_prefix}/profile{size}.png",
                extra_args={"ContentType": "image/png"},
            )
            urls[str(size)] = self.s3_client.build_url(key)
        return urls
