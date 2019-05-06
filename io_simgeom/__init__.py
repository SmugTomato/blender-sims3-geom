bl_info = {
    "name": "Sims 3 GEOM Tools",
    "category": "Import-Export",
	"version": (0, 11),
	"blender": (2, 80, 0),
	"location": "File > Import/Export",
	"description": "Importer and exporter for Sims 3 GEOM(.simgeom) files"
}

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

from .rigimport import RigImport
from .geomimport import GeomImport
from .geomexport import GeomExport
from .util.globals import Globals
from .operators import SIMGEOM_OT_recalc_ids, SIMGEOM_OT_split_seams
from .ui import SIMGEOM_PT_utility_panel

rootdir = os.path.dirname(os.path.realpath(__file__))
Globals.init(rootdir)

# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(GeomImport.bl_idname, text="Sims 3 GEOM (.simgeom)")
    self.layout.operator(RigImport.bl_idname, text="Sims 3 Rig (.grannyrig)")

def menu_func_export(self, context):
    self.layout.operator(GeomExport.bl_idname, text="Sims 3 GEOM (.simgeom)")

def register():
    bpy.utils.register_class(GeomImport)
    bpy.utils.register_class(GeomExport)
    bpy.utils.register_class(RigImport)
    bpy.utils.register_class(SIMGEOM_OT_recalc_ids)
    bpy.utils.register_class(SIMGEOM_OT_split_seams)
    bpy.utils.register_class(SIMGEOM_PT_utility_panel)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(GeomImport)
    bpy.utils.unregister_class(GeomExport)
    bpy.utils.unregister_class(RigImport)
    bpy.utils.unregister_class(SIMGEOM_OT_recalc_ids)
    bpy.utils.unregister_class(SIMGEOM_OT_split_seams)
    bpy.utils.unregister_class(SIMGEOM_PT_utility_panel)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()