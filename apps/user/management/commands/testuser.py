from django.core.management.base import BaseCommand
import sys
import os

from apps.user.utils.store import UserStore

# 테스트 유저 출력
class Command(BaseCommand):
    help = "테스트 환경 출력해줌"
    path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "testuser.xdat")
            )
    
    # testcase
    def handle(self, *args, **options):
        user = UserStore(self.path,"miku@example.com","cutemiku",is_default=True)
        sys.stdout.write(str(user))
