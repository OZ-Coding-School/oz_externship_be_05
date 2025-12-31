from __future__ import annotations

import configparser
from pathlib import Path
from typing import Any

from rest_framework.exceptions import APIException
from rest_framework.response import Response

_CONFIG_PATH = Path(__file__).with_name("messages.cfg")
_CONFIG_CACHE: configparser.ConfigParser | None = None


def _load_config() -> configparser.ConfigParser:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE
    parser = configparser.ConfigParser()
    parser.optionxform = str
    if _CONFIG_PATH.exists():
        parser.read(_CONFIG_PATH, encoding="utf-8")
    _CONFIG_CACHE = parser
    return parser


def _extract_country_code(request: Any) -> str:
    if request is None:
        return "KR"
    headers = getattr(request, "headers", None)
    if headers is not None:
        value = headers.get("X-Country-Code") or headers.get("X-Country")  # type: ignore[call-arg]
        if isinstance(value, str) and value:
            return value.upper()
    meta = getattr(request, "META", None)
    if isinstance(meta, dict):
        value = meta.get("HTTP_X_COUNTRY_CODE") or meta.get("HTTP_X_COUNTRY")
        if isinstance(value, str) and value:
            return value.upper()
    return "KR"


def _render_template(template: str, variables: dict[str, Any]) -> str:
    rendered = template
    for key, value in variables.items():
        rendered = rendered.replace(f"&{key}&", str(value))
    return rendered


def resolve_message(message_code: str, request: Any, variables: dict[str, Any]) -> str:
    config = _load_config()
    country_code = _extract_country_code(request)
    message = message_code
    section = None
    if config.has_section(country_code):
        section = config[country_code]
    elif config.has_section("KR"):
        section = config["KR"]
    if section is not None:
        template = section.get(message_code)
        if template:
            message = _render_template(template, variables)
    return message


class ResponseMessage(Response):
    def __init__(
        self,
        request: Any,
        status_code: int,
        message_code: str,
        **variables: Any,
    ) -> None:
        message = resolve_message(message_code, request, variables)
        detail_key = "error_detail" if str(status_code).startswith(("4", "5")) else "detail"
        data = {detail_key: message}
        super().__init__(data, status=status_code)


class MagicException(APIException):
    def __init__(self, *, status_code: int, message_code: str, **variables: object) -> None:
        self.status_code = status_code
        self.message_code = message_code
        self.variables = variables
        super().__init__(detail=message_code)
