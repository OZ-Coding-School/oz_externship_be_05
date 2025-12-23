import struct
import zlib
from typing import Optional

def get_test_config() -> Optional[str]:
    with open("apps/user/utils/testdata.xdat", "rb") as f:
        blob = f.read()

    if blob[:4] != b"XDAT":
        return None

    KEY  = struct.unpack(">H", blob[4:6])[0]
    SIZE = struct.unpack(">I", blob[6:10])[0]

    X2 = blob[10 : 10 + SIZE][::-1]
    X1  = bytes(b ^ (KEY & 0xFF) for b in X2)

    return zlib.decompress(X1).decode("utf-8")

print(get_test_config())