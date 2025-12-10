from datetime import datetime
from random import randint


class MockData:
    @staticmethod
    def mock_session() -> list[dict[str, str | int]]:
        return [
            {
                "id": i,
                "user": randint(50, 55) + i,
                "question": randint(1, 100),
                "title": f"dummy title {i}",
                "using_model": "openai",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            for i in range(5)
        ]

    @staticmethod
    def mock_session_post(
        question: int | str = "",
        title: str = "",
        using_model: str = "",
    ) -> dict[str, str | int]:
        return {
            "id": randint(1, 100),
            "user": randint(50, 55) + randint(1, 100),
            "question": question,
            "title": title,
            "using_model": using_model,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

    @staticmethod
    def mock_completion(session_id: int, message: str = "") -> dict[str, str | int]:
        return {
            "id": randint(1, 100),
            "session": session_id or randint(1, 100),
            "message": message or f"mock message {"id"}",
            "role": "user",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
