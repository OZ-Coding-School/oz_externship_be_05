from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from django.utils.dateparse import parse_date

from apps.user.models.user import GenderChoices, RoleChoices


class Command(BaseCommand):
    help = "db에 유저를 만들어줌다"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("email")
        parser.add_argument("password")
        parser.add_argument("name")
        parser.add_argument("phone_number")
        parser.add_argument("gender", choices=[choice.value for choice in GenderChoices])
        parser.add_argument("birthday", help="YYYY-MM-DD")
        parser.add_argument("--nickname")
        parser.add_argument("--role", choices=[choice.value for choice in RoleChoices], default=RoleChoices.USER)
        parser.add_argument("--inactive", action="store_true")
        parser.add_argument("--staff", action="store_true")
        parser.add_argument("--superuser", action="store_true")

    def handle(self, *args: Any, **options: Any) -> None:
        email = options["email"]
        password = options["password"]
        name = options["name"]
        phone_number = options["phone_number"]
        gender = options["gender"]
        birthday_raw = options["birthday"]

        birthday = parse_date(birthday_raw)
        if not birthday:
            raise CommandError("birthday must be in YYYY-MM-DD format")

        extra_fields = {
            "nickname": options.get("nickname"),
            "phone_number": phone_number,
            "gender": gender,
            "birthday": birthday,
            "is_active": not options.get("inactive", False),
        }

        is_superuser = options.get("superuser", False)
        is_staff = options.get("staff", False) or is_superuser

        try:
            if is_superuser:
                user = get_user_model().objects.create_superuser(
                    email=email,
                    password=password,
                    name=name,
                    is_staff=True,
                    **extra_fields,
                )
            else:
                user = get_user_model().objects.create_user(
                    email=email,
                    password=password,
                    name=name,
                    role=options.get("role"),
                    is_staff=is_staff,
                    **extra_fields,
                )
        except IntegrityError as exc:
            raise CommandError(f"failed to create user: {exc}") from exc

        self.stdout.write(self.style.SUCCESS(f"created user id={user.id} email={user.email}"))
