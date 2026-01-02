from __future__ import annotations

import io
import os
from typing import Any
from urllib.parse import urlparse

from PIL import Image, ImageOps
from rest_framework.exceptions import APIException

from apps.core.utils.s3_client import S3Client


class ImageResizer:
    # 뭔가 센터링이라던지 환경변수 더 받아오게 만들까 싶은데 귀찮아서 스킵
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

    def delete_all_by_id_path(self, image_url: str | None) -> None:
        """
        URL에서 폴더(PK) 경로를 추출하여 해당 폴더 내의 모든 파일 삭제합니다.
        """
        if not image_url:
            return

        try:
            parsed_url = urlparse(image_url)
            full_path = parsed_url.path.lstrip("/")
            folder_prefix = os.path.dirname(full_path)  # ex) "uploads/images/thumbnail/15"

            if folder_prefix:
                self.s3_client.delete_prefix(prefix=folder_prefix)

            print(f"S3 폴더 삭제 요청 완료: {folder_prefix}")

        except Exception as e:
            print(f"S3 이미지 폴더 삭제 실패: {e}")
