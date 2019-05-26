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

from io_simgeom.models.geom       import Geom
from io_simgeom.models.vertex     import Vertex
from io_simgeom.util.bytereader   import ByteReader
from io_simgeom.util.globals      import Globals


class GeomLoader:
    

    @staticmethod
    def readGeom(filepath: str) -> Geom:
        geomdata = None
        with open(filepath, "rb") as f:
            geomdata = f.read()

        meshdata    = Geom()
        reader      = ByteReader(geomdata)

        # RCOL Header Starts here
        reader.skip(12)
        _external_count = reader.getUint32()
        _internal_count = reader.getUint32()

        meshdata.internal_chunks = []
        for _ in range(_internal_count):
            meshdata.internal_chunks.append( GeomLoader.getITG(reader) )
        meshdata.external_resources = []
        for _ in range(_external_count):
            meshdata.external_resources.append( GeomLoader.getITG(reader) )
        meshdata.internal_locations = []
        for _ in range(_internal_count):
            meshdata.internal_locations.append( GeomLoader.getChunkInfo(reader) )

        # GEOM Chunk Starts here
        reader.skip(16)
        _embeddedID = reader.getUint32()
        meshdata.embeddedID = hex(_embeddedID)
        if _embeddedID != 0:
            meshdata.embeddedID = Globals.get_shader_name(_embeddedID)
            reader.skip(4*4)
            _shader_param_count = reader.getUint32()
            meshdata.shaderdata = GeomLoader.getShaderParamaters(reader, _shader_param_count)
        
        meshdata.merge_group    = reader.getUint32()
        meshdata.sort_order     = reader.getUint32()
        vertex_count            = reader.getUint32()
        element_count           = reader.getUint32()

        meshdata.element_data   = GeomLoader.getElementData(reader, element_count, vertex_count)
        meshdata.faces          = GeomLoader.getGroupData(reader)

        meshdata.skin_controller_index = reader.getUint32()
        meshdata.bones          = GeomLoader.getBones(reader)

        tgicount = int( reader.getUint32() )
        meshdata.tgi_list = []
        for _ in range(tgicount):
            meshdata.tgi_list.append( GeomLoader.getTGI(reader) )

        return meshdata
    

    @staticmethod
    def getFloatList(reader: ByteReader, count: int) -> list:
        data = []
        for _ in range(count):
            data.append(reader.getFloat())
        return data

    
    @staticmethod
    def getByteList(reader: ByteReader, count: int) -> list:
        data = []
        for _ in range(count):
            data.append(reader.getByte())
        return data


    @staticmethod
    def getTGI(reader: ByteReader) -> dict:
        tgi = {'type': None, 'group': None, 'instance': None}

        tgi['type']     = Globals.padded_hex(reader.getUint32(), 4)
        tgi['group']    = Globals.padded_hex(reader.getUint32(), 4)
        tgi['instance'] = Globals.padded_hex(reader.getUint64(), 8)

        return tgi


    @staticmethod
    def getITG(reader: ByteReader) -> dict:
        tgi = {'type': None, 'group': None, 'instance': None}

        tgi['instance'] = Globals.padded_hex(reader.getUint64(), 8)
        tgi['type']     = Globals.padded_hex(reader.getUint32(), 4)
        tgi['group']    = Globals.padded_hex(reader.getUint32(), 4)

        return tgi
    

    @staticmethod
    def getChunkInfo(reader: ByteReader) -> dict:
        info = {'position': None, 'size': None}

        info['position'] = reader.getUint32()
        info['size']     = reader.getUint32()

        return info
    

    @staticmethod
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
                    # entry['data'] = reader.getRaw(20)
                    reader.skip(20)
        return parameters
    

    @staticmethod
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
                    vertex.position = GeomLoader.getFloatList(reader, 3)
                elif datatype == 2:
                    vertex.normal = GeomLoader.getFloatList(reader, 3)
                elif datatype == 3:
                    if not vertex.uv:
                        vertex.uv = [GeomLoader.getFloatList(reader, 2)]
                    else:
                        vertex.uv.append(GeomLoader.getFloatList(reader, 2))
                elif datatype == 4:
                    vertex.assignment = GeomLoader.getByteList(reader, 4)
                elif datatype == 5:
                    vertex.weights = GeomLoader.getFloatList(reader, 4)
                elif datatype == 6:
                    vertex.tangent = GeomLoader.getFloatList(reader, 3)
                elif datatype == 7:
                    vertex.tagvalue = GeomLoader.getByteList(reader, 4)
                elif datatype == 10:
                    vertex.vertex_id = [reader.getUint32()]
            vertices.append(vertex)

        return vertices
    

    @staticmethod
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


    @staticmethod
    def getBones(reader: ByteReader) -> list:
        bones = []

        count = reader.getUint32()
        for _ in range(count):
            bones.append(
                Globals.get_bone_name(reader.getUint32())
            )

        return bones