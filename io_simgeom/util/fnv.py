import ctypes

PRIME32 = 0x01000193
PRIME64 = 0x00000100000001B3
OFFSET32 = 0x811C9DC5
OFFSET64 = 0xCBF29CE484222325

def to_uint32(n: int) -> int:
    return ctypes.c_uint32(n).value

def to_uint64(n: int) -> int:
    return ctypes.c_uint64(n).value


def fnv32(string: str) -> int:
    bstring = bytes(string.lower(), 'utf-8')
    fnv_hash = OFFSET32
    for b in bstring:
        fnv_hash *= PRIME32
        fnv_hash ^= b
    return to_uint32(fnv_hash)


def fnv64(string: str) -> int:
    bstring = bytes(string.lower(), 'utf-8')
    fnv_hash = OFFSET64
    for b in bstring:
        fnv_hash *= PRIME64
        fnv_hash ^= b
    return to_uint64(fnv_hash)
