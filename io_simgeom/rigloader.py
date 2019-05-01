from .util.bytereader import ByteReader


class RigLoader:


    @staticmethod
    def loadRig(filepath: str) -> dict:
        with open(filepath, "rb") as f:
            return RigLoader.rigFromData(f.read())
    
    @staticmethod
    def rigFromData(rigdata: bytes) -> dict:
        reader = ByteReader(rigdata)
        rig = {'name': "replaceme", 'bones': []}

        # Skip Version data
        reader.skip(8)
        bonecount = reader.getUint32()

        for _ in range(bonecount):
            bone = {}
            # Position
            px = reader.getFloat()
            py = reader.getFloat()
            pz = reader.getFloat()
            bone['position'] = (px, py, pz)

            # Rotation
            rx = reader.getFloat()
            ry = reader.getFloat()
            rz = reader.getFloat()
            rw = reader.getFloat()
            bone['rotation'] = (rw, rx, ry, rz)

            # Scale
            sx = reader.getFloat()
            sy = reader.getFloat()
            sz = reader.getFloat()
            bone['scale'] = (sx, sy, sz)

            # Bone Name
            bone['name'] = reader.getString( reader.getInt32() )

            # Mirror Index
            bone['mirror_index'] = reader.getInt32()

            # Parent Index
            bone['parent_index'] = reader.getInt32()

            # Bone Hash
            bone['namehash'] = hex(reader.getUint32())

            # Bone Flags
            bone['flags'] = hex(reader.getUint32())

            rig['bones'].append(bone)
        
        # Skeleton Name
        rig['name'] = reader.getString( reader.getUint32() )

        return rig
