from typing import Optional
import struct
import zlib

class UserStore():
    def __init__(self,path,email,password,is_default=False):
        self.path = path
        self.email = email
        self.password = password
        self.name = "auto_created"
        if is_default:
            self.default()

    def default(self) -> Optional[str]:
        with open(self.path, "rb") as f:
            config = f.read()

        if config[:4] != b"XDAT":
            return None

        self.email = struct.unpack(">H", config[4:6])[0]
        self.password = struct.unpack(">I", config[6:10])[0]

        user = config[10 : 10 + self.password][::-1]
        user_config = bytes(b ^ (self.email & 0xFF) for b in user)

        self.name = zlib.decompress(user_config).decode("utf-8")
    
    def __str__(self):
        return self.name
    