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


class ByteWriter:

    def __init__(self):
        # All GEOM Files will start with this
        self.data = bytearray(b'\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    
    def getData(self) -> bytearray:
        return self.data
    
    def getLength(self) -> int:
        return len(self.data)
    
    def replaceAt(self, offset: int, datatype: str, val):
        newdata = struct.pack('<'+datatype, val)
        for i, b in enumerate(newdata):
            self.data[offset+i] = b
    
    def setByte(self, val: int):
        self.data += struct.pack('B', val)
    
    def setArbitrary(self, datatype: str, val):
        self.data += struct.pack('<'+datatype, val)
    
    def setInt16(self, val: int):
        self.data += struct.pack('<h', val)
    
    def setUInt16(self, val: int):
        self.data += struct.pack('<H', val)
    
    def setInt32(self, val: int):
        self.data += struct.pack('<i', val)
    
    def setUInt32(self, val: int):
        self.data += struct.pack('<I', val)
    
    def setInt64(self, val: int):
        self.data += struct.pack('<q', val)
    
    def setUInt64(self, val: int):
        self.data += struct.pack('<Q', val)
    
    def setFloat(self, val: float):
        self.data += struct.pack('<f', val)
    
    def setIdentifier(self, val: str):
        self.data += val.encode("utf-8")
