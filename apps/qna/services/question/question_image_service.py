from django.db import transaction

from apps.core.utils.s3_client import S3Client
from apps.qna.models import Question, QuestionImage
from apps.qna.utils.content_image_parser import extract_image_urls_from_content
from apps.qna.utils.s3_utils import extract_key_from_url, is_valid_s3_url


def sync_question_images(question: Question, content: str) -> None:
    """
    본문(Content)에 포함된 이미지 URL을 추출하여 DB 및 S3와 동기화합니다.
    DB에는 도메인이 제거된 S3 Key만 저장합니다.
    """
    s3_client = S3Client()

    # 1. 본문 파싱 (본문에는 마크다운/HTML 문법상 Full URL이 들어있음)
    raw_urls_in_content = set(extract_image_urls_from_content(content))

    # DB 저장용 Key
    current_keys_in_content = set()
    for url in raw_urls_in_content:
        # 우리 버킷 이미지만 관리 대상 (외부 이미지는 무시)
        if is_valid_s3_url(url):
            key = extract_key_from_url(url)
            if key:
                current_keys_in_content.add(key)

    # 2. DB 상태 확인(DB의 img_url 필드에는 Key만 저장되어 있음)
    existing_images_qs = QuestionImage.objects.filter(question=question)
    existing_keys = set(existing_images_qs.values_list("img_url", flat=True))

    # 3. 비교
    keys_to_delete = existing_keys - current_keys_in_content
    keys_to_add = current_keys_in_content - existing_keys

    # 4. 삭제
    if keys_to_delete:
        # DB에서 삭제
        existing_images_qs.filter(img_url__in=keys_to_delete).delete()

        # S3 파일 삭제
        def delete_s3_files() -> None:
            for key in keys_to_delete:
                s3_client.delete(key)

        transaction.on_commit(delete_s3_files)

    # 5. 추가 (DB 저장)
    new_images = []
    for key in keys_to_add:
        new_images.append(QuestionImage(question=question, img_url=key))

    if new_images:
        QuestionImage.objects.bulk_create(new_images)
