import json

class Globals:
    # Shader Paramater Datatypes
    FLOAT = 1
    INTEGER = 2
    TEXTURE = 4

    HASHMAP: dict
    CAS_INDICES: dict

    @staticmethod
    def init(rootdir: str):
        datadir = rootdir + "/data/json/"
        with open(datadir + "hashmap.json", "r") as data:
            Globals.HASHMAP = json.loads(data.read())
        with open(datadir + "variables.json", "r") as data:
            Globals.CAS_INDICES = json.loads(data.read())['cas_indices']
    
    @staticmethod
    def get_bone_name(fnv32hash: int) -> str:
        return Globals.HASHMAP['bones'][hex(fnv32hash)]
    
    @staticmethod
    def get_shader_name(fnv32hash: int) -> str:
        return Globals.HASHMAP['shader'][hex(fnv32hash)]