import struct
import zlib
from typing import Any


# db rawdata 삽입/편집 규격(자동화/콘솔용)
class UserStore:

    name: Any
    email: Any
    password: Any

    def __init__(self, config_path: str, is_default: bool = False) -> None:
        self.config_path = config_path
        if is_default:
            with open(self.config_path, "rb") as f:
                config = f.read()

            if config[:4] != b"XDAT":
                return None

            # 바이너리 데이터에서 바이트 불러오기 (약속된 규약)
            self.email = struct.unpack(">H", config[4:6])[0]
            self.password = struct.unpack(">I", config[6:10])[0]

            # 유저 역참조로 바이너리 불러오기
            user = config[10 : 10 + self.password][::-1]
            # 콘픽파일 생성
            user_config = bytes(b ^ (self.email & 0xFF) for b in user)
            # 이름은 utf-8 변환 (디버깅/출력용)
            self.name = zlib.decompress(user_config).decode("utf-8")

    def set_meta(self, name: str, email: str, password: str) -> None:
        self.name = name
        self.email = email
        self.password = password

    def __str__(self) -> str:
        return str(self.name)
