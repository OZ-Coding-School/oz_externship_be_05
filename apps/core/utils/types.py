from typing import Any, Optional

from rest_framework.exceptions import ValidationError


def to_int(key: str, value: Any) -> Optional[int]:
    """
    value를 int로 변환한다.
    - None, "" 는 None 반환
    - 변환 불가능하면 ValidationError 발생
    """

    if value in (None, ""):
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{key} is not an integer")
