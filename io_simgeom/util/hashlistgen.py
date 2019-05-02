import json
from .fnv import fnv32, fnv64
from ..rigloader import RigLoader


strings = [
    'SimEyelashes', 'SimEyes', 'SimHair', 'SimSkin',
    'reflectivity', 'index_of_refraction', 'AlphaMap', 'Ambient',
    'Diffuse', 'DiffuseMap', 'Emission', 'HaloLowColor',
    'HaloRamp', 'NormalRamp', 'Reflective', 'RootColor', 
    'Shininess', 'SpecCompositeTexture', 'Specular', 'SpecularMap',
    'Transparency', 'Transparent', 'NormalMapScale', 'HighlightColor',
    'HaloHighColor', 'SpecStyle', 'NormalMap'
]

def shaderhashes() -> dict:
    hashdict = {}

    for s in strings:
        hash = fnv32(s)
        hashdict[hex(hash)] = s

    return hashdict

def bonehashes() -> dict:
    rigs = [
        "ac", "ad", "ah", "al", "au", "cc", "cd", "ch", "cu", "pu"
    ]
    hashes = {}

    for r in rigs:
        rigdata = RigLoader.loadRig("io_simgeom/data/rigs/" + r + "Rig.grannyrig")

        for b in rigdata['bones']:
            h = hex(fnv32(b['name']))
            hashes[h] = b['name']
    
    return hashes

def write_hashmap(filename: str):
    hashmap = {}

    hashmap['shader'] = shaderhashes()
    hashmap['bones'] = bonehashes()

    with open("io_simgeom/data/json/" + filename + ".json", "w+") as f:
        f.write(
            json.dumps(
                hashmap,
                indent=4
            )
        )