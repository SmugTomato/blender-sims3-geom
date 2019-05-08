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

# Set Current Working Directory to addon root folder
# This needs to be done to find the included data files

import os

import bpy

from .rigimport     import SIMGEOM_OT_import_rig
from .geomimport    import SIMGEOM_OT_import_geom
from .geomexport    import SIMGEOM_OT_export_geom
from .ui            import SIMGEOM_PT_utility_panel
from .operators     import *
from .util.globals  import Globals

bl_info = {
    "name": "Sims 3 GEOM Tools (Blender 2.80)",
    'author': "SmugTomato",
    "category": "Import-Export",
	"version": (0, 12),
	"blender": (2, 80, 0),
	"location": "File > Import/Export",
	"description": "Importer and exporter for Sims 3 GEOM(.simgeom) files"
}

rootdir = os.path.dirname(os.path.realpath(__file__))
Globals.init(rootdir)

classes = [
    SIMGEOM_PT_utility_panel,
    SIMGEOM_OT_import_rig,
    SIMGEOM_OT_import_geom,
    SIMGEOM_OT_export_geom,
    SIMGEOM_OT_import_rig_helper,
    SIMGEOM_OT_clean_groups,
    SIMGEOM_OT_recalc_ids,
    SIMGEOM_OT_split_seams
]

# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(SIMGEOM_OT_import_geom.bl_idname, text="Sims 3 GEOM (.simgeom)")
    self.layout.operator(SIMGEOM_OT_import_rig.bl_idname, text="Sims 3 Rig (.grannyrig)")

def menu_func_export(self, context):
    self.layout.operator(SIMGEOM_OT_export_geom.bl_idname, text="Sims 3 GEOM (.simgeom)")

def register():
    for item in classes:
        bpy.utils.register_class(item)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    for item in classes:
        bpy.utils.unregister_class(item)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()