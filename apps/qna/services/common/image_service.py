from django.db import transaction
from apps.core.utils.s3_client import S3Client
from apps.qna.models import Question, QuestionImage

from apps.qna.utils.content_image_parser import extract_image_urls_from_content
from apps.qna.utils.s3_utils import extract_key_from_url, is_valid_s3_url

def sync_question_images(question: Question, content: str) -> None:
    """
    본문(Content)에 포함된 이미지 URL을 추출하여 DB 및 S3와 동기화(삭제 및 추가)를 수행합니다.
    """
    s3_client = S3Client()

    # 1. 본문 파싱
    current_urls_in_content = set(extract_image_urls_from_content(content))

    # 2. DB 상태 확인
    existing_images_qs = QuestionImage.objects.filter(question=question)
    existing_images_map = {img.img_url: img for img in existing_images_qs}
    existing_urls = set(existing_images_map.keys())

    # 3. 비교 (Diff)
    urls_to_delete = existing_urls - current_urls_in_content
    urls_to_add = current_urls_in_content - existing_urls

    # 4. 삭제 처리
    if urls_to_delete:
        existing_images_qs.filter(img_url__in=urls_to_delete).delete()

        def delete_s3_files():
            for url in urls_to_delete:
                key = extract_key_from_url(url)
                if key:
                    s3_client.delete(key)

        transaction.on_commit(delete_s3_files)

    # 5. 추가 처리
    new_images = []
    for url in urls_to_add:
        if is_valid_s3_url(url):
            new_images.append(QuestionImage(question=question, img_url=url))

    if new_images:
        QuestionImage.objects.bulk_create(new_images)