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