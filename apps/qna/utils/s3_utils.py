from urllib.parse import urlparse
from django.conf import settings

def extract_key_from_url(url: str) -> str:
    """
    S3 URL에서 객체 Key를 추출합니다.
    예: https://my-bucket.s3.ap-northeast-2.amazonaws.com/folder/image.jpg
        -> folder/image.jpg
    """
    if not url:
        return ""

    parsed = urlparse(url)
    return parsed.path.lstrip("/")

def is_valid_s3_url(url: str) -> bool:
    """
    주어진 URL이 우리 프로젝트의 S3 버킷 URL인지 검증합니다.
    """
    if not url:
        return False

    # settings에서 버킷 이름 가져오기
    bucket_name = getattr(settings, "AWS_S3_BUCKET_NAME", "")

    # 1. 버킷 이름이 포함되어 있는지
    # 2. AWS 도메인인지 (커스텀 도메인을 쓴다면 이 부분 로직을 settings.AWS_S3_CUSTOM_DOMAIN 비교로 변경해야 함)
    return bucket_name in url and "amazonaws.com" in url