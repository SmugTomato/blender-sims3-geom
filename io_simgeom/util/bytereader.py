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

import struct


class ByteReader:

    def __init__(self, data):
        self.data = data
        self.offset = 0
    
    def skip(self, bytes_to_skip: int):
        self.offset += bytes_to_skip
    
    def setOffset(self, offset: int):
        self.offset = offset
    
    def getOffset(self) -> int:
        return self.offset
    
    def getByte(self) -> int:
        byte = self.data[self.offset]
        self.offset += 1
        return byte
    
    def getInt16(self) -> int:
        bytes = bytearray()
        for _ in range(2):
            bytes.append(self.getByte())
        return struct.unpack('<h', bytes)[0]
    
    def getUint16(self) -> int:
        bytes = bytearray()
        for _ in range(2):
            bytes.append(self.getByte())
        return struct.unpack('<H', bytes)[0]
    
    def getInt32(self) -> int:
        bytes = bytearray()
        for _ in range(4):
            bytes.append(self.getByte())
        return struct.unpack('<i', bytes)[0]
    
    def getUint32(self) -> int:
        bytes = bytearray()
        for _ in range(4):
            bytes.append(self.getByte())
        return struct.unpack('<I', bytes)[0]
    
    def getInt64(self) -> int:
        bytes = bytearray()
        for _ in range(8):
            bytes.append(self.getByte())
        return struct.unpack('<q', bytes)[0]
    
    def getUint64(self) -> int:
        bytes = bytearray()
        for _ in range(8):
            bytes.append(self.getByte())
        return struct.unpack('<Q', bytes)[0]
    
    def getFloat(self) -> float:
        bytes = bytearray()
        for _ in range(4):
            bytes.append(self.getByte())
        return struct.unpack('<f', bytes)[0]
    
    def getRaw(self, length: int) -> bytearray:
        bytes = bytearray()
        for _ in range(length):
            bytes.append(self.getByte())
        return bytes
    
    def getString(self, length: int) -> str:
        return self.getRaw(length).decode('utf-8')
