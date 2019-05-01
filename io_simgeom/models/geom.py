

class Geom:


    def __init__(self):
        # RCOL Header data
        self.internal_chunks: list    # TGI tables
        self.external_resources: list  # TGI tables
        self.internal_locations: list

        # GEOM data
        self.tgi_list: list
        self.embeddedID = str
        self.shaderdata: list      # MTNF(Shader Paramaters) Chunk if embeddedID != 0
        self.merge_group: int
        self.sort_order: int
        self.element_data: list
        self.groups: list          # Should generally only be 1, but could be more
        self.skin_controller_index: int
        self.bones: list
    
    
    def dataDump(self) -> dict:
        ob = {
            'RCOL_HEADER': {
                'internal_chunks': self.internal_chunks,
                'external_resources': self.external_resources,
                'internal_locations': self.internal_locations
            },
            'GEOM_DATA': {
                'tgi_list': self.tgi_list,
                'mergegroup': self.merge_group,
                'sortorder': self.sort_order,
                'skincontroller': self.skin_controller_index,
                'embedded_id': self.embeddedID,
                'shaderdata': self.shaderdata,
                'vertexdata': self.element_data,
                'faces': self.groups,
                'bones': self.bones
            }
        }

        return ob
