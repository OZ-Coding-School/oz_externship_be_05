from typing import TypedDict

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


class CategoryPath(TypedDict):
    id: int
    path: str


def build_category_path(category: QuestionCategory) -> CategoryPath:
    names: list[str] = []

    current: QuestionCategory | None = category
    while current is not None:
        names.append(current.name)
        current = current.parent

    return {
        "id": category.id,
        "path": " > ".join(reversed(names)),
    }
