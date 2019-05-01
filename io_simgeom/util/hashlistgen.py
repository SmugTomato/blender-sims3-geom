import json
from .fnv import fnv32, fnv64


strings = [
    'SimEyelashes', 'SimEyes', 'SimHair', 'SimSkin',
    'reflectivity', 'index_of_refraction', 'AlphaMap', 'Ambient',
    'Diffuse', 'DiffuseMap', 'Emission', 'HaloLowColor',
    'HaloRamp', 'NormalRamp', 'Reflective', 'RootColor', 
    'Shininess', 'SpecCompositeTexture', 'Specular', 'SpecularMap',
    'Transparency', 'Transparent', 'NormalMapScale', 'HighlightColor',
    'HaloHighColor', 'SpecStyle', 'NormalMap'
]


def generate_hashlist():
    hashdict = {}

    for s in strings:
        hash = fnv32(s)
        hashdict[hex(hash)] = s
    
    f = open('io_sims3geom/util/json/hashmap.json', 'w+')
    data = json.dumps(hashdict, indent=4)
    f.write(data)
    f.close()

generate_hashlist()