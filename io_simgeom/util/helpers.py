import json

from io_simgeom.util.bytereader import ByteReader
from io_simgeom.util.bytewriter import ByteWriter
from io_simgeom.util.globals import Globals
from io_simgeom.models.vertex import Vertex

def padded_hex(value: int, numbytes: int):
    return "0x{0:0{1}X}".format(value, numbytes * 2)

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

    tgi['type'] = padded_hex(reader.getUint32(), 4)
    tgi['group'] = padded_hex(reader.getUint32(), 4)
    tgi['instance'] = padded_hex(reader.getUint64(), 8)

    return tgi


def getITG(reader: ByteReader) -> dict:
    tgi = {'type': None, 'group': None, 'instance': None}

    tgi['instance'] = padded_hex(reader.getUint64(), 8)
    tgi['type'] = padded_hex(reader.getUint32(), 4)
    tgi['group'] = padded_hex(reader.getUint32(), 4)

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
        entry['name'] = Globals.get_shader_name(reader.getUint32())
        entry['type'] = reader.getUint32()
        entry['size'] = reader.getUint32()
        reader.skip(4)
        parameters.append(entry)
    for entry in parameters:
        if entry['type'] == Globals.FLOAT:
            data = []
            for _ in range(entry['size']):
                data.append( reader.getFloat() )
            entry['data'] = data
        elif entry['type'] == Globals.INTEGER:
            data = []
            for _ in range(entry['size']):
                data.append( reader.getInt32() )
            entry['data'] = data
        elif entry['type'] == Globals.TEXTURE:
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
        vertex = Vertex()
        for datatype in datatypes:
            if datatype == 1:
                vertex.position = getFloatList(reader, 3)
            elif datatype == 2:
                vertex.normal = getFloatList(reader, 3)
            elif datatype == 3:
                # TODO: Can 1 vertex even have 2 UV Channels?
                vertex.uv = getFloatList(reader, 2)
            elif datatype == 4:
                vertex.assignment = getByteList(reader, 4)
            elif datatype == 5:
                vertex.weights = getFloatList(reader, 4)
            elif datatype == 6:
                vertex.tangent = getFloatList(reader, 3)
            elif datatype == 7:
                vertex.tagvalue = getByteList(reader, 4)
            elif datatype == 10:
                vertex.vertex_id = [reader.getUint32()]
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
            Globals.get_bone_name(reader.getUint32())
        )

    return bones