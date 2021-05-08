# Copyright (C) 2019 SmugTomato
# 
# This file is part of BlenderGeom.
# 
# BlenderGeom is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# BlenderGeom is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with BlenderGeom.  If not, see <http://www.gnu.org/licenses/>.

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
        fnv_hash = (fnv_hash * PRIME32) & 0xffffffff
        fnv_hash ^= b
    return to_uint32(fnv_hash)


def fnv64(string: str) -> int:
    bstring = bytes(string.lower(), 'utf-8')
    fnv_hash = OFFSET64
    for b in bstring:
        fnv_hash = (fnv_hash * PRIME64) & 0xffffffffffffffff
        fnv_hash ^= b
    return to_uint64(fnv_hash)
