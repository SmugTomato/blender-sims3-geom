#!/usr/bin/python

import os
import re
import json
import zipfile

base_path = os.path.dirname(os.path.realpath(__file__))
config_path = f"{base_path}/io_simgeom/__init__.py"

def zipdir(path, ziph):
    for root, dirs, files in os.walk(path):
        for file in files:
            if not ".pyc" in file:
                fullpath = os.path.join(root, file)
                relpath = os.path.relpath(fullpath, base_path)
                ziph.write(fullpath, relpath)

with open(config_path, "r") as f:
    contents = f.read()
    s = re.compile("bl_info\s+=\s+").split(contents)[1]
    s = re.findall("\{[^}]*\}", s)[0]
    s = str.replace(s, '(', '[')
    s = str.replace(s, ')', ']')
    
    j = json.loads(s)
    version = j.get('version', [0, 0, 0])

    version_string = ""
    for val in version:
        version_string += str(val) + "."
    
    zip_name = f"BlenderGeom_{version_string}zip"

    zipf = zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_LZMA)
    zipdir(f"{os.path.dirname(os.path.realpath(__file__))}/io_simgeom", zipf)
    zipf.write(os.path.join(base_path, "LICENSE"), os.path.relpath(os.path.join(base_path, "io_simgeom/LICENSE"), base_path))
    zipf.close()

    print(f"Packaged {zip_name} succesfully")
