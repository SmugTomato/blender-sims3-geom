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

from .models.geom       import Geom
from .models.vertex     import Vertex
from .util.bytewriter   import ByteWriter
from .util              import fnv

"""
Write out a new GEOM File sequentially
REQUIRED INFO CAN BE FOUND HERE
http://simswiki.info/wiki.php?title=Sims_3:RCOL
http://simswiki.info/wiki.php?title=Sims_3:0x015A1849
http://simswiki.info/wiki.php?title=Sims_3:0x01D0E75D
http://simswiki.info/wiki.php?title=Sims_3:Key_table
"""
class GeomWriter:


    @staticmethod
    def writeGeom(filepath: str, geomData: Geom) -> None:
        with open(filepath, "wb+") as f:
            f.write(GeomWriter.buildData(geomData))
    

    @staticmethod
    def buildData(geomData: Geom) -> bytearray:
        b = ByteWriter()

        # RCOL HEADER
        b.setUInt32( len(geomData.external_resources) )
        b.setUInt32( len(geomData.internal_chunks) )
        for i in range(len(geomData.internal_chunks)):
            b.setUInt64( int(geomData.internal_chunks[i]['instance'], 0) )
            b.setUInt32( int(geomData.internal_chunks[i]['type'], 0) )
            b.setUInt32( int(geomData.internal_chunks[i]['group'], 0) )
        for i in range(len(geomData.external_resources)):
            b.setUInt64( int(geomData.internal_chunks[i]['instance'], 0) )
            b.setUInt32( int(geomData.internal_chunks[i]['type'], 0) )
            b.setUInt32( int(geomData.internal_chunks[i]['group'], 0) )
        b.setUInt32( b.getLength() + 8 )    # The start of the GEOM Chunk is in 2 more DWORDs
        chunksize_offset = b.getLength()    # save Chunk size byte offset
        b.setUInt32(0xFFFFFFFF)             # GEOM Chunk size will have to be replaced when everything is written

        # GEOM HEADER
        b.setIdentifier("GEOM")             # Chunk identifier
        b.setUInt32(5)                      # Version is always 5
        tgi_offset = b.getLength()          # will have to be replaced when everything is written
        b.setUInt32(0xFFFFFFFF)             # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        tgilen = 4 + len(geomData.tgi_list) * 16
        b.setUInt32(tgilen)                 # TGI Size

        # MTNF DATA
        if geomData.embeddedID != hex(0):
            b.setUInt32( fnv.fnv32(geomData.embeddedID) )
            mtnfsize_offset = b.getLength()
            b.setUInt32(0xFFFFFFFF)             # MTNF Chunk Size will have to be calculated after it has been written
            b.setIdentifier("MTNF")
            b.setUInt64(0x0000007400000000)     # unknown DWORD, WORD, WORD; Seem to always be these values
            b.setUInt32( len(geomData.shaderdata) )
            offset = 16 + len(geomData.shaderdata) * 16
            # Shader parameter info
            for d in geomData.shaderdata:
                b.setUInt32( fnv.fnv32(d['name']) )
                b.setUInt32( d['type'] )
                b.setUInt32( d['size'] )
                b.setUInt32(offset)
                # Calculate offsets based on datasizes
                offset += d['size'] * 4
            # Shader parameters
            for d in geomData.shaderdata:
                if d['type'] == 1:
                    for entry in d['data']:
                        b.setFloat(entry)
                elif d['type'] == 2:
                    for entry in d['data']:
                        b.setUInt32(entry)
                elif d['type'] == 4:
                    if d['size'] == 4:
                        b.setUInt64(d['data'])
                        b.setUInt64(0)
                    elif d['size'] == 5:
                        pass
            # Replace MTNF Chunksize data, -4 to go back to the start location of the DWORD
            b.replaceAt( mtnfsize_offset, 'I', b.getLength() - mtnfsize_offset - 4 )
        else:
            b.setUInt32(0)

        # GEOM DATA
        b.setUInt32(geomData.merge_group)
        b.setUInt32(geomData.sort_order)
        b.setUInt32(len(geomData.element_data))         # Vertex Count

        order = GeomWriter.set_vertex_info(geomData.element_data[0], b)
        # Set the values for vertex data
        for vertex in geomData.element_data:
            uv_layer = 0
            for entry in order:
                var = getattr(vertex, entry[0])
                if entry[0] == 'uv':
                    var = getattr(vertex, entry[0])[uv_layer]
                for val in var:
                    b.setArbitrary(entry[1], val)

        b.setUInt32(1)
        b.setByte(2)
        b.setUInt32(len(geomData.faces) * 3)
        for face in geomData.faces:
            for vert in face:
                b.setUInt16(vert)
        b.setUInt32(geomData.skin_controller_index)
        b.setUInt32(len(geomData.bones))
        for bone in geomData.bones:
            b.setUInt32(fnv.fnv32(bone))
        b.replaceAt(tgi_offset, 'I', b.getLength() - tgi_offset - 4)    # Replace TGI Offset with the proper value
        b.setUInt32(len(geomData.tgi_list))
        for tgi in geomData.tgi_list:
            b.setUInt32( int(tgi['type'], 0) )
            b.setUInt32( int(tgi['group'], 0) )
            b.setUInt64( int(tgi['instance'], 0) )
        b.replaceAt(chunksize_offset, 'I', b.getLength() - chunksize_offset - 4)    # Replace GEOM Chunk Size value
        # GEOM File is now successfully written

        return b.getData()
    

    @staticmethod
    def set_vertex_info(vertex: Vertex, writer: ByteWriter) -> list:
        datatypes = {
            'position':     [1,  1, 12, 'f'],
            'normal':       [2,  1, 12, 'f'],
            'uv':           [3,  1, 8,  'f'],
            'assignment':   [4,  2, 4,  'B'],
            'weights':      [5,  1, 16, 'f'],
            'tangent':      [6,  1, 12, 'f'],
            'tagvalue':     [7,  3, 4,  'B'],
            'vertex_id':    [10, 4, 4,  'I'],
        }

        order = []

        for key, values in datatypes.items():
            if getattr(vertex, key):
                if key == 'uv':
                    for _ in range(len(vertex.uv)):
                        order.append([key, values[3]])
                else:
                    order.append([key, values[3]])
        writer.setUInt32(len(order))    # Element Count
        for item in order:
            values = datatypes[item[0]]
            writer.setUInt32(values[0])
            writer.setUInt32(values[1])
            writer.setByte(values[2])
        
        return order