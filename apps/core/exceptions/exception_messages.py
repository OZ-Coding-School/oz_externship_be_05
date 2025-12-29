from typing import Callable, Dict, Final

ErrorDetail = Dict[str, str]
DynamicMessage = Callable[..., ErrorDetail]


class ErrorMessages:
    """
    프로젝트 전역에서 사용하는 Error Messages 관리 클래스입니다.
    딕셔너리 형태 {"error_detail": "메시지"}를 반환합니다.

    구조:
    1. 고정 메시지: 변수 없이 문자열로 바로 사용 (예: ERR.E401_LOGIN_REQUIRED)
    2. 동적 메시지: 람다(lambda) 함수를 호출하여 동적으로 생성 (예: ERR.E404_NOT_FOUND("게시글"))

    접두사 규칙:
    - E400: Bad Request (잘못된 요청)
    - E401: Unauthorized (인증 필요)
    - E403: Forbidden (권한 거부)
    - E404: Not Found (찾을 수 없음)
    - E409: Conflict (데이터 충돌)
    - E410: Gone (만료됨)
    - E423: Locked (잠김)
    """

    # --- 400 Bad Request ---
    E400_EXAM_CODE_MISMATCH: Final[ErrorDetail] = {"error_detail": "응시 코드가 일치하지 않습니다."}
    E400_CATEGORY_REQUIRED: Final[ErrorDetail] = {"error_detail": "카테고리 종류와 이름은 필수 입력값입니다."}
    E400_QUESTION_ID_REQUIRED: Final[ErrorDetail] = {"error_detail": "question_id는 필수 쿼리 파라미터입니다."}
    E400_INVALID_PHONE_FORMAT: Final[ErrorDetail] = {"error_detail": "11자리 숫자로 구성된 포맷이어야 합니다."}
    E400_REQUIRED_FIELD: Final[ErrorDetail] = {"error_detail": "이 필드는 필수 항목입니다."}
    E400_EMAIL_AUTH_INVALID: Final[ErrorDetail] = {"error_detail": "이메일 인증 실패 - 인증코드가 유효하지 않습니다."}
    E400_INVALID_FILE_FORMAT: Final[ErrorDetail] = {"error_detail": "잘못된 파일 형식입니다."}
    E400_ASSISTANT_REQUIRED_FIELD: Final[ErrorDetail] = {"error_detail": "조교 권한 변경 시 필수 필드입니다."}
    E400_PHONE_AUTH_INVALID: Final[ErrorDetail] = {"error_detail": "휴대폰 인증 실패 - 인증코드가 유효하지 않습니다."}
    E400_LENGTH_LIMIT: DynamicMessage = lambda target, min_l, max_l: {
        "error_detail": f"{target}은(는) {min_l}~{max_l}자 사이여야 합니다."
    }
    E400_INVALID_REQUEST: DynamicMessage = lambda action: {"error_detail": f"유효하지 않은 {action} 요청입니다."}
    E400_INVALID_DATA: DynamicMessage = lambda action: {"error_detail": f"유효하지 않은 {action} 데이터입니다."}
    E400_INVALID_SESSION: DynamicMessage = lambda target: {"error_detail": f"유효하지 않은 {target} 세션입니다."}

    # --- 401 Unauthorized ---
    E401_LOGIN_REQUIRED: Final[ErrorDetail] = {"error_detail": "로그인이 필요합니다."}
    E401_NO_AUTH_DATA: Final[ErrorDetail] = {"error_detail": "자격 인증 데이터가 제공되지 않았습니다."}
    E401_USER_ONLY_ACTION: DynamicMessage = lambda action: {
        "error_detail": f"로그인한 사용자만 {action}할 수 있습니다."
    }
    E401_STUDENT_ONLY_ACTION: DynamicMessage = lambda action: {
        "error_detail": f"로그인한 수강생만 {action}할 수 있습니다."
    }

    # --- 403 Forbidden ---
    E403_ADOPT_OWNER_ONLY: Final[ErrorDetail] = {"error_detail": "본인이 작성한 질문의 답변만 채택할 수 있습니다."}
    E403_SESSION_EXPIRED: Final[ErrorDetail] = {"error_detail": "로그인 세션이 만료되었습니다."}
    E403_PERMISSION_DENIED: DynamicMessage = lambda action: {"error_detail": f"{action} 권한이 없습니다."}
    E403_OWNER_ONLY_EDIT: DynamicMessage = lambda target: {
        "error_detail": f"본인이 작성한 {target}만 수정할 수 있습니다."
    }
    E403_QNA_PERMISSION_DENIED: DynamicMessage = lambda action: {"error_detail": f"질의응답 {action} 권한이 없습니다."}
    E403_QUIZ_PERMISSION_DENIED: DynamicMessage = lambda action: {"error_detail": f"쪽지시험 {action} 권한이 없습니다."}
    E403_ACCOUNT_WITHDRAWN: DynamicMessage = lambda expire: {"error_detail": f"탈퇴 신청한 계정입니다. {expire}"}

    # --- 404 Not Found ---
    E404_NO_QUESTIONS_AVAILABLE: Final[ErrorDetail] = {"error_detail": "조회 가능한 질문이 존재하지 않습니다."}
    E404_NO_EXAM_HISTORY: Final[ErrorDetail] = {"error_detail": "조회된 응시 내역이 없습니다."}
    E404_CHATBOT_SESSION_NOT_FOUND: Final[ErrorDetail] = {"error_detail": "챗봇 세션이 존재하지 않습니다."}
    E404_USER_CHATBOT_SESSION_NOT_FOUND: Final[ErrorDetail] = {"error_detail": "해당 질문에 대한 챗봇 세션이 없습니다."}
    E404_NOT_FOUND: DynamicMessage = lambda target: {"error_detail": f"{target}을(를) 찾을 수 없습니다."}
    E404_NOT_EXIST: DynamicMessage = lambda target: {"error_detail": f"등록된 {target}이(가) 없습니다."}

    # --- 409 Conflict ---
    E409_DUPLICATE_DISTRIBUTION: Final[ErrorDetail] = {"error_detail": "동일한 조건의 배포가 이미 존재합니다."}
    E409_QUIZ_LIMIT_EXCEEDED_EDIT: Final[ErrorDetail] = {
        "error_detail": "제한 수 또는 총 배점을 초과하여 수정할 수 없습니다."
    }
    E409_ALREADY_ADOPTED: Final[ErrorDetail] = {"error_detail": "이미 채택된 답변이 존재합니다."}
    E409_AI_ALREADY_RESPONDED: Final[ErrorDetail] = {"error_detail": "이미 AI가 답변을 생성했습니다."}
    E409_QUIZ_LIMIT_EXCEEDED_REG: Final[ErrorDetail] = {
        "error_detail": "등록 가능한 문제 수 또는 총 배점을 초과했습니다."
    }
    E409_PHONE_DUPLICATE_FAILED: Final[ErrorDetail] = {"error_detail": "휴대폰 번호 중복으로 요청 처리에 실패했습니다."}

    E409_CANNOT_DELETE_DEFAULT: DynamicMessage = lambda target: {
        "error_detail": f"기본 {target}은(는) 삭제할 수 없습니다."
    }
    E409_DUPLICATE_NAME: DynamicMessage = lambda target: {
        "error_detail": f"동일한 이름의 {target}이(가) 이미 존재합니다."
    }
    E409_CONFLICT_ON_ACTION: DynamicMessage = lambda action: {"error_detail": f"{action} 중 충돌이 발생했습니다."}
    E409_ALREADY_REGISTERED: DynamicMessage = lambda target: {"error_detail": f"이미 등록된 {target}입니다."}
    E409_ALREADY_SUBMITTED: DynamicMessage = lambda target: {"error_detail": f"이미 제출된 {target}입니다."}
    E409_ALREADY_EXISTS_HISTORY: DynamicMessage = lambda target: {
        "error_detail": f"이미 중복된 {target} 내역이 존재합니다."
    }
    E409_DUPLICATE_EXIST: DynamicMessage = lambda target: {"error_detail": f"중복된 {target}이(가) 존재합니다."}

    # --- 410 Gone ---
    E410_ALREADY_ENDED: DynamicMessage = lambda target: {"error_detail": f"{target}이(가) 이미 종료되었습니다."}
    E410_ENDED: DynamicMessage = lambda target: {"error_detail": f"{target}이(가) 종료되었습니다."}

    # --- 423 Locked ---
    E423_LOCKED: DynamicMessage = lambda action: {"error_detail": f"아직 {action}할 수 없습니다."}


EMS = ErrorMessages
