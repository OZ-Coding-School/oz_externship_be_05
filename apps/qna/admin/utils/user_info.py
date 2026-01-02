from typing import Any

from django.utils.html import format_html
from django.utils.safestring import SafeString, mark_safe


def get_user_display_info(user: Any) -> SafeString:
    """
    [답변 목록 표시용] 유저 Role에 따라 (썸네일 + 닉네임 + 과정/직함) 정보를 HTML로 반환
    """
    if not user:
        return mark_safe("-")

    nickname = getattr(user, "nickname", "")
    if not nickname:
        nickname = getattr(user, "name", "이름 없음")

    profile_url = getattr(user, "profile_image_url", "")
    role = getattr(user, "role", "U")

    # 썸네일 이미지 HTML (없으면 회색 원)
    if profile_url:
        img_html = f'<img src="{profile_url}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; margin-right: 12px; border: 1px solid #e0e0e0;">'
    else:
        img_html = '<div style="display:inline-block; width: 40px; height: 40px; border-radius: 50%; background-color: #ccc; margin-right: 12px; vertical-align: middle;"></div>'

    info_text = ""

    # [A] 수강생 (ST) & 조교 (TA) -> 과정 및 기수 정보 필요
    if role in ["ST", "TA"]:
        target_obj = None

        try:
            if role == "ST":
                # 수강생: 현재 진행 중인 수강 정보 가져오기
                target_obj = getattr(user, "in_progress_cohortstudent", None)

            elif role == "TA":
                # 조교: 담당하고 있는 기수 정보 가져오기
                if hasattr(user, "trainingassistant_set"):
                    target_obj = user.trainingassistant_set.select_related("cohort__course").first()
        except Exception:
            target_obj = None

        # 기수/과정명 파싱
        course_name = ""
        generation = ""

        if target_obj and hasattr(target_obj, "cohort"):
            cohort = target_obj.cohort
            course_name = getattr(cohort.course, "name", "")
            if hasattr(cohort, "number"):
                generation = f"{cohort.number}기"

        course_info = f"{course_name} {generation}".strip()

        if role == "ST":
            info_text = course_info
        else:
            # 과정 정보가 없으면 그냥 "조교"만 출력
            info_text = f"{course_info} 조교".strip() if course_info else "조교"

    else:
        if role == "LC":
            info_text = "러닝 코치"
        elif role == "OM":
            info_text = "교육 운영 매니저"
        elif role == "AD":
            info_text = "관리자"
        else:
            info_text = "일반 회원"

    # 만약 정보가 비어있다면 시스템 기본 역할명으로 대체
    if not info_text:
        info_text = user.get_role_display()

    return format_html(
        """
        <div style="display: flex; align-items: center; padding: 5px 0;">
            {img}
            <div style="display: flex; flex-direction: column; justify-content: center;">
                <span style="font-weight: bold; font-size: 14px; color: inherit; line-height: 1.2;">{nick}</span>
                <span style="font-size: 12px; color: #666; margin-top: 4px;">{info}</span>
            </div>
        </div>
        """,
        img=mark_safe(img_html),
        nick=nickname,
        info=info_text,
    )
