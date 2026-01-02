from typing import Any

from django.utils.html import format_html
from django.utils.safestring import mark_safe


def get_user_display_info(user: Any) -> str:
    """
    유저의 Role에 따라 (썸네일 + 닉네임 + 과정/직함) 정보를 HTML로 반환
    """

    if not user:
        return "-"

    # 1. 기본 정보 추출
    # User 모델에 nickname 필드가 없거나 비어있을 경우를 대비해 name을 fallback으로 사용
    nickname = getattr(user, "nickname", "")
    if not nickname:
        nickname = getattr(user, "name", "이름 없음")

    profile_url = getattr(user, "profile_image_url", "")
    role = getattr(user, "role", "U")

    # 2. 썸네일 이미지 HTML 생성
    if profile_url:
        img_html = f'<img src="{profile_url}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; margin-right: 12px; border: 1px solid #e0e0e0;">'
    else:
        # 이미지가 없을 경우 회색 원으로 대체
        img_html = '<div style="display:inline-block; width: 40px; height: 40px; border-radius: 50%; background-color: #ccc; margin-right: 12px; vertical-align: middle;"></div>'

    # 3. 텍스트 정보 구성 (과정명, 기수, 직함)
    info_text = ""

    # 3-1. 과정/기수 정보 추출 로직
    target_obj = None
    role = getattr(user, "role", "U")

    try:
        if role == "ST":  # Student
            target_obj = getattr(user, "in_progress_cohortstudent", None)
    except Exception:
        target_obj = None

    # 추출된 객체에서 데이터 파싱
    course_name = ""
    generation = ""

    if target_obj and hasattr(target_obj, "cohort"):
        cohort = target_obj.cohort
        course_name = getattr(cohort.course, "name", "")
        generation = f"{cohort.number}기" if hasattr(cohort, "number") else ""

        # 4. 역할별 최종 텍스트 포맷팅 수정
    if role == "ST":
        info_text = f"{course_name} {generation}".strip()
    elif role == "TA":
        info_text = "조교"
    elif role == "LC":
        info_text = "러닝 코치"
    elif role == "OM":
        info_text = "교육 운영 매니저"
    elif role == "AD":
        info_text = "관리자"
    else:
        info_text = "일반 회원"

        # 최종 출력 시에도 정보가 아예 없다면 기본 역할명 표시
    if not info_text.strip():
        info_text = user.get_role_display()

    # 5. HTML 조립
    return format_html(
        '''
        <div style="display: flex; align-items: center; padding: 5px 0;">
            {img}
            <div style="display: flex; flex-direction: column; justify-content: center;">
                <span style="font-weight: bold; font-size: 14px; color: inherit; line-height: 1.2;">{nick}</span>
                <span style="font-size: 12px; color: #666; margin-top: 4px;">{info}</span>
            </div>
        </div>
        ''',
        img=mark_safe(img_html),
        nick=nickname,
        info=info_text
    )