"""
核心签名算法
============
场馆 API 请求参数签名: 字典序拼接 + 固定密钥 MD5。
"""

import hashlib
import json
from typing import Any

SIGN_KEY = "BwPimfkcRKAmHcbL9tnq"  # 硬编码密钥


def md5(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


def build_sign(params: dict[str, Any]) -> str:
    """
    签名生成:

    1. 按 key 字典序排序
    2. 跳过 None、空字符串
    3. bool -> "true"/"false"(小写)
    4. dict/list -> JSON 序列化(无空格, ensure_ascii=False)
    5. 拼接 "key=value&key=value..."
    6. 末尾加密钥 -> MD5
    """
    keys = sorted(params.keys())
    pairs: list[str] = []
    for k in keys:
        v = params[k]
        if v is None:
            continue
        if isinstance(v, (dict, list)):
            val = json.dumps(v, ensure_ascii=False, separators=(",", ":"))
        elif isinstance(v, bool):
            val = "true" if v else "false"
        else:
            val = str(v).strip()
        if val == "":
            continue
        pairs.append(f"{k}={val}")
    return md5("&".join(pairs) + SIGN_KEY)
