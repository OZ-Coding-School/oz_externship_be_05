from django.db import transaction

from apps.core.utils.s3_client import S3Client
from apps.qna.models import Question, QuestionImage


def sync_question_images(question: Question, content: str, extract_image_urls_from_content=None) -> None:
    """
    본문(Content)에 포함된 이미지 URL을 추출하여 DB 및 S3와 동기화(삭제 및 추가)를 수행합니다.
    """
    s3_client = S3Client()

    # 1. 본문 파싱
    current_urls_in_content = extract_image_urls_from_content(content)

    # 2. DB 상태 확인
    existing_images_map = {img.img_url: img for img in QuestionImage.objects.filter(question=question)}
    existing_urls = set(existing_images_map.keys())

    # 3. 비교 (Diff)
    urls_to_delete = existing_urls - current_urls_in_content
    urls_to_add = current_urls_in_content - existing_urls

    # 4. 삭제 처리 (S3 파일 삭제 + DB 삭제)
    if urls_to_delete:
        # 1. DB 먼저 삭제
        QuestionImage.objects.filter(question=question, img_url__in=urls_to_delete).delete()

        # 2. S3 삭제는 트랜잭션이 성공적으로 끝난 뒤에 실행 예약
        def delete_s3_files():
            for url in urls_to_delete:
                s3_client.delete_from_url(url)

        transaction.on_commit(delete_s3_files)

    # 5. 추가 처리 (검증 + DB 저장)
    new_images = []
    for url in urls_to_add:
        if s3_client.is_valid_s3_url(url):
            new_images.append(QuestionImage(question=question, img_url=url))

    if new_images:
        QuestionImage.objects.bulk_create(new_images)
