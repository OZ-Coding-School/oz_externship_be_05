import re
from typing import Set


def extract_image_urls_from_content(content: str) -> Set[str]:
    """
    HTML/Markdown 본문에서 <img src="..."> 또는 마크다운 이미지 링크를 추출
    """

    html_pattern = r'<img[^>]+src="([^">]+)"'

    urls = set(re.findall(html_pattern, content))
    return urls
