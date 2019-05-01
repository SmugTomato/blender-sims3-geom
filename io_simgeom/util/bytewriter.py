import struct


class ByteWriter:

    def __init__(self):
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