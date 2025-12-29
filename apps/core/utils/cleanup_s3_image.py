from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Iterator, List, TypeVar, Tuple, Type

from django.core.management.base import BaseCommand
from django.db.models import Model
from mypy_boto3_s3 import S3Client
from mypy_boto3_s3.type_defs import DeleteTypeDef, ObjectIdentifierTypeDef
# 관리할 모델 임포트
from apps.qna.models.answer.images import AnswerImage


from apps.core.utils.s3_client import S3Client as MyS3ClientWrapper

T = TypeVar("T")


def chunked(iterable: Iterable[T], size: int = 1000) -> Iterator[List[T]]:
    source = list(iterable)
    for i in range(0, len(source), size):
        yield source[i : i + size]


class Command(BaseCommand):
    help = "Remove orphaned answer images from S3"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="실제 삭제는 수행하지 않고, 삭제 대상 파일 목록만 출력합니다.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        is_dry_run = options["dry_run"]
        mode_text = "[DRY RUN]" if is_dry_run else "[REAL]"
        self.stdout.write(f"{mode_text} 가비지 컬렉션을 시작합니다...")

        wrapper = MyS3ClientWrapper()
        s3_client: S3Client = wrapper.s3
        bucket_name = wrapper.bucket_name

        safety_boundary = datetime.now(timezone.utc) - timedelta(hours=24)
        # 청소대상 목록
        targets: List[Tuple[str, Type[Model]]] = [
            ("answer_images/", AnswerImage),

        ]
        total_scanned = 0
        total_deleted = 0

        for prefix, model_class in targets:
            self.stdout.write(f"\n🚀 [{prefix}] 구역 스캔 중... ({model_class.__name__})")


            paginator = s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

            for page in pages:
                if "Contents" not in page:
                    continue

                orphans, scanned_count = self._find_orphans_in_page(
                    page["Contents"], 
                    safety_boundary,
                    model_class
                )
                
                total_scanned += scanned_count

                if not orphans:
                    continue

                deleted_count = self._process_batch_deletion(s3_client, bucket_name, orphans, is_dry_run)
                total_deleted += deleted_count

        self.stdout.write(self.style.SUCCESS(f"작업 종료! 총 스캔: {total_scanned}, 총 삭제: {total_deleted}"))

    def _find_orphans_in_page(
            self, 
            contents: List[Any], 
            safety_boundary: datetime,
            model_class: Type[Model]
    ) -> tuple[List[str], int]:
        
        candidates: List[str] = []
        scanned = 0

        for obj in contents:
            scanned += 1
            if obj.get("LastModified") >= safety_boundary:
                continue

            key = obj.get("Key")
            if key:
                candidates.append(key)

        if not candidates:
            return [], scanned

        # 모든 모델의 필드가 image_url
        existing_keys = set(model_class.objects.filter(image_url__in=candidates).values_list("image_url", flat=True))
        orphan_keys = set(candidates) - existing_keys
        return list(orphan_keys), scanned

    def _process_batch_deletion(self, s3: S3Client, bucket: str, keys: List[str], is_dry_run: bool) -> int:
        deleted_count = 0

        for chunk in chunked(keys, size=1000):
            if is_dry_run:
                self.stdout.write(self.style.WARNING(f"👀 [Dry Run] 삭제 대상 발견: {len(chunk)}개 (실행 안 됨)"))
                deleted_count += len(chunk)
                continue

            count = self._delete_chunk_safely(s3, bucket, chunk)
            deleted_count += count

        return deleted_count

    def _delete_chunk_safely(self, s3: S3Client, bucket: str, chunk: List[str]) -> int:
        try:
            objects: List[ObjectIdentifierTypeDef] = [{"Key": k} for k in chunk]
            delete_req: DeleteTypeDef = {"Objects": objects}

            response = s3.delete_objects(Bucket=bucket, Delete=delete_req)

            deleted = len(response.get("Deleted", []))
            errors = response.get("Errors", [])

            if errors:
                for err in errors:
                    self.stdout.write(self.style.ERROR(f"❌ 삭제 실패: {err.get('Key')} ({err.get('Code')})"))

            self.stdout.write(f"🔥 {deleted}개 삭제 완료")
            return deleted

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"💥 S3 API 호출 중 치명적 오류: {e}"))
            return 0
