from .models.geom import Geom
from .util.bytereader import ByteReader
from .util.helpers import HASHMAP, getTGI, getITG, getChunkInfo, getShaderParamaters, getElementData, getGroupData, getBones


class GeomLoader:
    

    @staticmethod
    def readGeom(filepath: str) -> Geom:
        _geomfile = open(filepath, "rb")
        geomdata = _geomfile.read()
        _geomfile.close()

        meshdata = Geom()
        reader = ByteReader(geomdata)


        # RCOL Header Starts here
        reader.skip(12)
        _external_count = reader.getUint32()
        _internal_count = reader.getUint32()

        meshdata.internal_chunks = []
        for _ in range(_internal_count):
            meshdata.internal_chunks.append( getITG(reader) )
        meshdata.external_resources = []
        for _ in range(_external_count):
            meshdata.external_resources.append( getITG(reader) )
        meshdata.internal_locations = []
        for _ in range(_internal_count):
            meshdata.internal_locations.append( getChunkInfo(reader) )
        

        # GEOM Chunk Starts here
        reader.skip(16)
        _embeddedID = reader.getUint32()
        meshdata.embeddedID = hex(_embeddedID)
        if _embeddedID != 0:
            meshdata.embeddedID = HASHMAP.getName(_embeddedID, "shader")
            reader.skip(4*4)
            _shader_param_count = reader.getUint32()
            meshdata.shaderdata = getShaderParamaters(reader, _shader_param_count)
        
        meshdata.merge_group = reader.getUint32()
        meshdata.sort_order = reader.getUint32()
        vertex_count = reader.getUint32()
        element_count = reader.getUint32()

        meshdata.element_data = getElementData(reader, element_count, vertex_count)
        meshdata.groups = getGroupData(reader)

        meshdata.skin_controller_index = reader.getUint32()
        meshdata.bones = getBones(reader)

        tgicount = int( reader.getUint32() )
        meshdata.tgi_list = []
        for _ in range(tgicount):
            meshdata.tgi_list.append( getTGI(reader) )

        return meshdata