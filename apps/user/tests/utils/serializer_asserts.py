from __future__ import annotations

from datetime import date, datetime
from typing import Any, Mapping, Protocol

from django.utils.dateparse import parse_datetime


class _TestCaseLike(Protocol):
    def assertEqual(self, first: object, second: object, msg: str | None = None) -> None: ...
    def assertTrue(self, expr: object, msg: str | None = None) -> None: ...
    def assertIsNone(self, obj: object, msg: str | None = None) -> None: ...
    def assertIsNotNone(self, obj: object, msg: str | None = None) -> None: ...


class SerializerAssertsMixin:
    def assert_keys_exact(self: _TestCaseLike, data: Mapping[str, Any], expected_keys: set[str]) -> None:
        self.assertEqual(set(data.keys()), expected_keys)

    def assert_keys_contains(self: _TestCaseLike, data: Mapping[str, Any], expected_keys: set[str]) -> None:
        self.assertTrue(expected_keys.issubset(set(data.keys())))

    def assert_date_str(self: _TestCaseLike, value: str | None, expected: date | None) -> None:
        if expected is None:
            self.assertIsNone(value)
            return
        self.assertEqual(value, expected.isoformat())

    def assert_datetime_str(self: _TestCaseLike, value: str, expected: datetime) -> None:
        parsed = parse_datetime(value)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(int(parsed.timestamp()), int(expected.timestamp()))
