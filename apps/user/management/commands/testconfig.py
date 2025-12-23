from django.core.management.base import BaseCommand
from typing import Optional
import struct
import zlib
import sys
import os

# 뭔가 수상한 테스트 콘픽 출력
class Command(BaseCommand):
    help = "테스트 설정 파일 출력해줌"
    path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "testconfig.xdat")
            )
    
    def handle(self, *args, **options):
        text = self.test_config_to_str()
        if text is None:
            self.stderr.write("파일 누락")
            return

        sys.stdout.write(text)

    def test_config_to_str(self) -> Optional[str]:

        with open(self.path, "rb") as f:
            blob = f.read()

        if blob[:4] != b"XDAT":
            return None

        KEY  = struct.unpack(">H", blob[4:6])[0]
        SIZE = struct.unpack(">I", blob[6:10])[0]

        data = blob[10 : 10 + SIZE][::-1]
        raw  = bytes(b ^ (KEY & 0xFF) for b in data)

        return zlib.decompress(raw).decode("utf-8")
