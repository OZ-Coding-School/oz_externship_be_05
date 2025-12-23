import os
import sys
from typing import Any

from django.core.management.base import BaseCommand

from apps.user.utils.store import UserStore


# 테스트 유저 출력
class Command(BaseCommand):
    help = "테스트 환경 출력해줌"
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "testuser.xdat"))

    # testcase
    def handle(self, *args: Any, **options: Any) -> None:
        user = UserStore(self.path, is_default=True)
        sys.stdout.write(f"{str(user)}")
