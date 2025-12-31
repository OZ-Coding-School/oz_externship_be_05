import re


def extract_image_urls_from_content(content: str) -> list[str]:
    """
    본문에서 이미지 URL을 추출
    Markdown 형식(![...](url)) / HTML 형식(<img src="url">)
    """
    if not content:
        return []

    urls = set()

    # 1. 마크다운 이미지 문법: ![대체텍스트](이미지URL)
    markdown_pattern = r"!\[.*?\]\((https?://.*?)\)"
    urls.update(re.findall(markdown_pattern, content))

    # 2. HTML 이미지 태그: <img ... src="이미지URL" ... >
    html_pattern = r'<img[^>]+src="([^">]+)"'
    urls.update(re.findall(html_pattern, content))

    return list(urls)
