import json
import os

from io_simgeom.util.bytereader import ByteReader

class NameFromHash:

    def __init__(self):
        self.hashmap = None
        with open(os.getcwd() + "/data/json/hashmap.json", "r") as data:
            self.hashmap = json.loads(data.read())
    
    def getName(self, hash: int, key: str):
        return self.hashmap[key][hex(hash)]

FLOAT = 1
INTEGER = 2
TEXTURE = 4
HASHMAP = NameFromHash()

def getFloatList(reader: ByteReader, count: int) -> list:
    data = []
    for _ in range(count):
        data.append(reader.getFloat())
    return data


def getByteList(reader: ByteReader, count: int) -> list:
    data = []
    for _ in range(count):
        data.append(reader.getByte())
    return data


def getTGI(reader: ByteReader) -> dict:
    tgi = {'type': None, 'group': None, 'instance': None}

    tgi['type'] = reader.getUint32()
    tgi['group'] = reader.getUint32()
    tgi['instance'] = reader.getUint64()

    return tgi


def getITG(reader: ByteReader) -> dict:
    tgi = {'type': None, 'group': None, 'instance': None}

    tgi['instance'] = reader.getUint64()
    tgi['type'] = reader.getUint32()
    tgi['group'] = reader.getUint32()

    return tgi


def getChunkInfo(reader: ByteReader) -> dict:
    info = {'position': None, 'size': None}

    info['position'] = reader.getUint32()
    info['size'] = reader.getUint32()

    return info


def getShaderParamaters(reader: ByteReader, count: int) -> list:
    parameters = []
    for _ in range(count):
        entry = {'name': None, 'type': None, 'size': None, 'data': None}
        entry['name'] = HASHMAP.getName(reader.getUint32(), "shader")
        entry['type'] = reader.getUint32()
        entry['size'] = reader.getUint32()
        reader.skip(4)
        parameters.append(entry)
    for entry in parameters:
        if entry['type'] == FLOAT:
            data = []
            for _ in range(entry['size']):
                data.append( reader.getFloat() )
            entry['data'] = data
        elif entry['type'] == INTEGER:
            data = []
            for _ in range(entry['size']):
                data.append( reader.getInt32() )
            entry['data'] = data
        elif entry['type'] == TEXTURE:
            if entry['size'] == 4:
                entry['data'] = reader.getUint32()
                reader.skip(12)
            elif entry['size'] == 5:
                entry['data'] = reader.getRaw(20)
    return parameters


def getElementData(reader: ByteReader, element_count: int, vert_count: int) -> list:
    vertices = []

    datatypes = []
    for _ in range(element_count):
        datatypes.append(reader.getUint32())
        reader.skip(5)
    
    for _ in range(vert_count):
        vertex = {}
        for datatype in datatypes:
            if datatype == 1:
                vertex['position'] = getFloatList(reader, 3)
            elif datatype == 2:
                vertex['normal'] = getFloatList(reader, 3)
            elif datatype == 3:
                vertex['uv'] = getFloatList(reader, 2)
            elif datatype == 4:
                vertex['assignment'] = getByteList(reader, 4)
            elif datatype == 5:
                vertex['weights'] = getFloatList(reader, 4)
            elif datatype == 6:
                vertex['tangent'] = getFloatList(reader, 3)
            elif datatype == 7:
                vertex['tagval'] = getByteList(reader, 4)
            elif datatype == 10:
                vertex['vertex_id'] = [reader.getUint32()]
        vertices.append(vertex)

    return vertices


def getGroupData(reader: ByteReader) -> list:
    faces = []
    reader.skip(5)

    numfacepoints = reader.getUint32()
    for _ in range( int(numfacepoints / 3) ):
        faces.append([
            reader.getInt16(),
            reader.getInt16(),
            reader.getInt16()
        ])

    return faces


def getBones(reader: ByteReader) -> list:
    bones = []

    count = reader.getUint32()
    for _ in range(count):
        bones.append(
            HASHMAP.getName( reader.getUint32(), "bones" )
        )

    return bones