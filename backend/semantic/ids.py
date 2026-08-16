from __future__ import annotations

import hashlib


def stable_id(
    namespace: str,
    value: str,
) -> int:
    raw = (
        f"{namespace}:{value.strip().lower()}"
        .encode("utf-8")
    )

    digest = hashlib.sha256(raw).digest()

    return (
        int.from_bytes(
            digest[:8],
            byteorder="big",
            signed=False,
        )
        & 0x7FFFFFFFFFFFFFFF
    )