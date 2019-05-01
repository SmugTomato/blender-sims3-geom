from io_simgeom.geomloader import GeomLoader
from io_simgeom.geomwriter import GeomWriter
from io_simgeom.rigloader import RigLoader
import json

meshdata = GeomLoader.readGeom("mesh/afBodyDressSunbelt/afBodyDressSunbelt_lod1_0x00000000D9DBB6AB.simgeom")
rigdata = RigLoader.loadRig("mesh/auRig.grannyrig")

GeomWriter.writeGeom("mesh/afBodyDressSunbelt/out.simgeom", meshdata)

