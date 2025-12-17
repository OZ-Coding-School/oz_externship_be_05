from typing import Any

from apps.qna.models import QuestionCategory


def get_descendant_category_ids(category_id: int) -> list[int]:
    ids: list[int] = []

    def collect_descendants(current_category_id: int) -> None:
        ids.append(current_category_id)

        children = QuestionCategory.objects.filter(parent_id=current_category_id)
        for child in children:
            collect_descendants(child.id)

    collect_descendants(category_id)
    return ids


def build_category_path(category: QuestionCategory) -> dict[str, Any]:
    names: list[str] = []

    current = category
    while current:
        names.append(current.name)
        assert current.parent is not None
        current = current.parent

    return {
        "id": category.id,
        "path": " > ".join(reversed(names)),
    }
