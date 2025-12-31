from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Literal, TypedDict, TypeVar, cast

from django.db.models import Count, Model, QuerySet
from django.db.models.functions import TruncMonth, TruncYear
from django.utils import timezone

Interval = Literal["monthly", "yearly"]
M = TypeVar("M", bound=Model)


class TrendItem(TypedDict):
    period: str
    count: int


@dataclass(frozen=True)
class TrendResult:
    interval: Interval
    from_date: date
    to_date: date
    total: int
    items: list[TrendItem]


def _first_day_of_month(d: date) -> date:
    return d.replace(day=1)


def _add_months(d: date, months: int) -> date:
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    return date(y, m, 1)


def get_trend(
    *,
    model: type[M],
    interval: Interval,
    years: int = 5,
    date_field: str = "created_at",
) -> TrendResult:
    today = timezone.localdate()

    manager = cast(Any, model).objects

    qs: QuerySet[M]
    items: list[TrendItem]

    if interval == "monthly":
        end_month = _first_day_of_month(today)
        start_month = _add_months(end_month, -11)
        end_exclusive = _add_months(end_month, 1)

        qs = cast(
            QuerySet[M],
            manager.filter(
                **{
                    f"{date_field}__date__gte": start_month,
                    f"{date_field}__date__lt": end_exclusive,
                }
            ),
        )

        rows = qs.annotate(p=TruncMonth(date_field)).values("p").annotate(count=Count("id"))

        bucket_month: dict[str, int] = {
            r["p"].date().strftime("%Y-%m"): int(r["count"]) for r in rows if r["p"] is not None
        }

        items = []
        cursor = start_month
        for _ in range(12):
            label = cursor.strftime("%Y-%m")
            items.append({"period": label, "count": bucket_month.get(label, 0)})
            cursor = _add_months(cursor, 1)

        total = sum(i["count"] for i in items)
        return TrendResult(
            interval="monthly",
            from_date=start_month,
            to_date=end_month,
            total=total,
            items=items,
        )

    # yearly
    current_year = today.year
    start_year = current_year - (years - 1)

    start_date = date(start_year, 1, 1)
    end_exclusive = date(current_year + 1, 1, 1)

    qs = cast(
        QuerySet[M],
        manager.filter(
            **{
                f"{date_field}__date__gte": start_date,
                f"{date_field}__date__lt": end_exclusive,
            }
        ),
    )

    rows = qs.annotate(p=TruncYear(date_field)).values("p").annotate(count=Count("id"))

    bucket_year: dict[str, int] = {str(r["p"].date().year): int(r["count"]) for r in rows if r["p"] is not None}

    items = []
    for y in range(start_year, current_year + 1):
        label = str(y)
        items.append({"period": label, "count": bucket_year.get(label, 0)})

    total = sum(i["count"] for i in items)
    return TrendResult(
        interval="yearly",
        from_date=start_date,
        to_date=date(current_year, 1, 1),
        total=total,
        items=items,
    )
