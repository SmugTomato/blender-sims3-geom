bl_info = {
    'name': 'Sims 3 RIG Editor',
    'author': 'cmomoney@MTS',
    'version': (0, 2),
    'blender': (2, 6, 2),
    'category': 'Import-Export',
    'location': 'File > Import/Export',
    'wiki_url': ''}

    # ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy, struct, mathutils, os, subprocess
from mathutils import *
from bpy.props import *

class FNV32(object):
    prime = 0x01000193
    offset = 0x811C9DC5
    @staticmethod
    def hash(string):
        h = FNV32.offset
        byteArray = str(string).lower().encode(encoding='ascii')
        for b in list(byteArray):
            h *= FNV32.prime
            h ^= b
            h &= 0xFFFFFFFF
        return h

class RIG_Panel(bpy.types.Panel):
    bl_label = 'Sims 3 RIG Editor'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'bone'
    
    @classmethod
    def poll(cls, context):
        return context.active_object != None and context.active_object.type == 'ARMATURE'
    
    def draw(self, context):
        
        l = self.layout
        scene = bpy.context.scene
        arm = context.object
        bone = bpy.context.active_bone
        
        row = l.row() 
        row.prop(arm, 'name')
        row = l.row()
        row.operator('add.bone', text='Add Bone')
        row = l.row(align=True)
        row.operator('name.tohash', text='Use Hash Names')
        row.operator('name.toreal', text='Use Real Names')
        if arm.mode == 'POSE' and bpy.context.active_pose_bone != None:
            row = l.row()
            box = row.box()
            box.label(text='Bone Details')
            box.prop(bone, 'realName')
            box.prop(bone, 'hashName')
            split = box.split()
            col = split.column()
            col.label(text='Parent:')
            col = split.column()
            col.prop_search(bone, "parent", arm.data, "edit_bones", text="")
        if arm.mode == 'EDIT':
            row = l.row()
            box = row.box()
            box.label(text='Bone Details')
            split = box.split()
            col = split.column()
            col = split.column()
            col.prop(bone, 'boneIndex')            
            box.prop(bone, 'realName')
            box.prop(bone, 'hashName')                        
            box.prop_search(bone, "parent", arm.data, "edit_bones", text="Parent")
            box.prop_search(bone, 'mirrorBone', arm.data, 'edit_bones', text='Mirror')            
            box.prop(bone, 'boneFlags')
        

class Add_Bone(bpy.types.Operator):
    bl_idname = 'add.bone'
    bl_label = 'Add Bone'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = 'Add bone to RIG'
    
    @classmethod
    def poll(cls, context):
        return context.active_object != None and context.active_object.type == 'ARMATURE'
          
    name = bpy.props.StringProperty(name="Name")    
    mirror = bpy.props.StringProperty(name='Mirror Index')
    flags = bpy.props.StringProperty(name='Flags value', default='00000023')
    hashName = bpy.props.BoolProperty(name='use hash name', default=False)
    
    def execute(self, context):
        rig = bpy.context.active_object
        bpy.ops.object.mode_set(mode='EDIT')
        bones = rig.data.bones.data.edit_bones
                
        bone = bones.new(self.name)
        bone.use_connect = False
        bone.use_deform = True
        bone.use_inherit_rotation = False
        bone.use_local_location = False
        bone.head = 0,0,0
        bone.tail = 0,0.05,0
        if self.mirror == '':
            ind = len(bones)
            bone.mirrorIndex = repr(ind-1)
        else:
            bone.mirrorIndex = self.mirror
        if self.hashName == True:
            bone.mirrorBone = bones[int(bone.mirrorIndex)].name
        bone.boneFlags = self.flags
        bone.boneIndex = len(bones)-1
        bone.parent = bones['transformBone']
        bpy.ops.object.mode_set(mode='OBJECT')
        bone.realName = self.name
        hash = FNV32.hash(self.name)
        hash = hex(hash)[2:]
        rig.data.bones[self.name].hashName = hash
        rig.data.bones[self.name].realName = self.name 
        if self.hashName == True:
            bone.name = '0x' + hash.upper()                 
        bpy.ops.object.mode_set(mode='POSE')
        return{'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class Hash_Names(bpy.types.Operator):
    bl_idname = 'name.tohash'
    bl_label = 'Bone names to hash'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object != None and context.active_object.type == 'ARMATURE'
    
    def execute(self, context):
        rig = bpy.context.active_object
        bpy.ops.object.mode_set(mode='EDIT')
        try:
            bpy.types.EditBone.hashName
        except:
            pass
        else:
            bpy.types.EditBone.hashName = bpy.props.StringProperty(name='Hash Name')
            bpy.types.EditBone.realName = bpy.props.StringProperty(name='Bone Name')
            
        for bone in rig.data.edit_bones:
            if bone.hashName != '':
                if bone.hashName[:2] == '0x':
                    bone.name = bone.hashName.upper()    
                else:
                    bone.name = '0x' + bone.hashName.upper()
            else:
                bone.realName = bone.name
                hash = FNV32.hash(bone.name)
                hash = hex(hash)[2:]
                bone.hashName = '0x' + hash.upper()
                bone.name = bone.hashName
                
                
        bpy.ops.object.mode_set(mode='OBJECT')
        return{'FINISHED'}
    
class Real_Names(bpy.types.Operator):
    bl_idname = 'name.toreal'
    bl_label = 'Use real names'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object != None and context.active_object.type == 'ARMATURE'
    
    def execute(self, context):
        rig = bpy.context.active_object
        bpy.ops.object.mode_set(mode='EDIT')
        for bone in rig.data.edit_bones:
            bone.name = bone.realName
        bpy.ops.object.mode_set(mode='OBJECT')
        return{'FINISHED'}

class RIG_Import(bpy.types.Operator):
    bl_idname = 'rig.importer'
    bl_label = 'Sims 3 Import RIG'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = 'Import Sims 3 RIG files'
    
    filepath = StringProperty(name="File path", description="File filepath used for importing the RIG file", maxlen=1024, default="")
    filter_folder = BoolProperty(name="Filter folders", description="", default=True, options={'HIDDEN'})
    filter_glob = StringProperty(default="*.grannyrig", options={'HIDDEN'})
    isBodyRig = BoolProperty(name='Body Rig', description='Import a body rig', default=False)
    useHexNames = BoolProperty(name='Use Hash Names', description='Use hash names for bones', default=False)
    useShape = BoolProperty(name='Use Shape', description='Use custom shape for bones')
    
    def execute(self, context):
        self.parsefile()
        return{'FINISHED'}
        
    def invoke(self, context, event):
        wm = context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def parsefile(self):
        # Open original file
        with open(self.filepath, 'rb') as f:                
            def read(s,l,size, hex=0):
                l = struct.unpack(l, f.read(size))[0]                            
                return l
            
            def readLong(s, hex=0):
                return read(s, 'l', 4, hex);
            
            def readQuad(s, hex=0):
                return read(s, 'q', 8, hex);
        
            def readByte(s, hex=0):
                return read(s, 'B', 1, hex);
            
            def readHex(s):
                thisHex = []
                for j in range(s):
                    a = f.read(1)
                    b = '%x' % ord(a)
                    c = repr(b)
                    if len(c) == 3:
                        c = ('0' + c[1:-1])
                    else:
                        c = (c[1:-1])
                    thisHex.append(c)
                k = thisHex
                if s == 4:
                    tHex = (k[3] + k[2] + k[1] + k[0])
                elif s == 8:
                    tHex = (k[7] + k[6] + k[5] + k[4] + k[3] + k[2] + k[1] + k[0])
                return tHex
            
                        
            positions = []
            rotations = []
            scalings = []
            bNames = []
            mirrors = []
            parentIndexes = []
            bnamesHash = []
            flags = []
            skeletonName = ''           
            
            majorVersion = readLong('MajorVersion')
            minorVersion = readLong('MinorVersion')
            boneCount    = readLong('BoneCount')  
            
            for i in range(boneCount):
                #get positions
                px = struct.unpack('f', f.read(4))
                py = struct.unpack('f', f.read(4))
                pz = struct.unpack('f', f.read(4))
                pos = (px[0], py[0], pz[0])
                positions.append(pos)
                
                #get rotations
                rx = struct.unpack('f', f.read(4))
                ry = struct.unpack('f', f.read(4))
                rz = struct.unpack('f', f.read(4))
                rw = struct.unpack('f', f.read(4))
                rot = (rw[0], rx[0], ry[0], rz[0])
                rotations.append(rot)
                
                #get scalings
                sx = struct.unpack('f', f.read(4))
                sy = struct.unpack('f', f.read(4))
                sz = struct.unpack('f', f.read(4))
                scl = (sx[0], sy[0], sz[0])
                scalings.append(scl)
                
                #get bone name
                nl = readLong('nameLength')
                s = []
                name = ''               
                for n in range(nl):
                    c = struct.unpack('s', f.read(1))
                    s.append(c[0].decode())
                name = name.join(s)
                print(name)
                bNames.append(name)
                
                mirror = readLong('mirrorIndex')
                mirrors.append(mirror)
                 
                #get parent index
                pi = readLong('ParentIndex')
                parentIndexes.append(pi)
                print(pi)
                
                #get bone hash name
                hn = readHex(4)
                print(hn)
                bnamesHash.append(hn)
                
                #get flags
                flag = readHex(4)
                flags.append(flag)
                print('')
                
            #get skeleton name
            sn = readLong('skeletonNameLength')
            s = []
            name = ''               
            for n in range(sn):
                c = struct.unpack('s', f.read(1))
                s.append(c[0].decode())
            skeletonName = name.join(s)  
            print(skeletonName)
            
            #create armature
            rig = bpy.data.objects.new(skeletonName, bpy.data.armatures.new(skeletonName))
            rig.data.use_deform_envelopes = False
            rig.data.draw_type = 'OCTAHEDRAL'
            bpy.context.scene.objects.link(rig)
            bpy.context.scene.objects.active = rig
            bpy.ops.object.mode_set(mode='POSE')
            bpy.types.EditBone.hashName = bpy.props.StringProperty(name='Hash Name')
            bpy.types.EditBone.realName = bpy.props.StringProperty(name='Bone Name')
            bpy.types.EditBone.mirrorIndex = bpy.props.StringProperty(name='Mirror Index')
            bpy.types.EditBone.mirrorBone = bpy.props.StringProperty(name='Mirror Bone')
            bpy.types.EditBone.boneFlags = bpy.props.StringProperty(name='Flags')
            bpy.types.EditBone.boneIndex = bpy.props.IntProperty(name='Bone Index')
            bpy.types.EditBone.hashName = bpy.props.StringProperty(name='Hash Name')
            bpy.types.EditBone.realName = bpy.props.StringProperty(name='Bone Name')
            bpy.types.Bone.hashName = bpy.props.StringProperty(name='Hash Name')
            bpy.types.Bone.realName = bpy.props.StringProperty(name='Bone Name')
            
            #add bones
            bpy.ops.object.mode_set(mode='EDIT')
            bones = rig.data.edit_bones
            c = 0
            for i in range(len(bNames)):
                if self.useHexNames == True:
                    bone = bones.new('0x' + bnamesHash[i].upper())
                else:    
                    bone = bones.new(bNames[i])
                if parentIndexes[i] >= 0:
                    bone.parent = bones[parentIndexes[i]]
                bone.use_connect = False
                bone.use_deform = True
                if self.isBodyRig == True:
                    bone.use_inherit_rotation = True
                    bone.head = 0,0,0
                    bone.tail = 0,0.01,0
                else:
                    bone.use_inherit_rotation = False
                    bone.head = 0,0,0
                    bone.tail = 0,0.05,0
                bone.use_local_location = False                
                bone.hashName = bnamesHash[i]
                bone.realName = bNames[i]
                bone.mirrorIndex = repr(mirrors[i])
                bone.boneFlags = flags[i]
                bone.boneIndex = c
                c += 1
                
            for i in bones:
                i.mirrorBone = bones[int(i.mirrorIndex)].name
            bpy.ops.object.mode_set(mode='POSE')
            
            #set bone positions in pose mode            
            for i in range(len(rig.pose.bones)):
                bone = rig.pose.bones[i]
                vector = Vector((positions[i][0], positions[i][1], positions[i][2]))
                bone.location = vector
                rot = Quaternion((rotations[i][0], rotations[i][1], rotations[i][2], rotations[i][3]))
                bone.rotation_quaternion = rot
                scale = Vector((scalings[i][0], scalings[i][1], scalings[i][2]))
            bpy.ops.pose.armature_apply()
            
            #set edit bone local to True
            bpy.ops.object.mode_set(mode='EDIT')
            for i in rig.data.edit_bones:
                i.use_local_location = True
                           
            #rotate for Blender's sake :P
            bpy.ops.object.mode_set(mode='OBJECT')            
            rig.rotation_euler = 1.5707963705062866,0,0
            rig.select = True
            for i in range(0, len(rig.data.bones)):
                rig.data.bones[i].hashName = bnamesHash[i]
                rig.data.bones[i].realName = bNames[i]
            
            
            #create and assign custom shape
            if self.useShape == True:
                bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,size=1)
                bone_vis = bpy.context.active_object
                bone_vis.data.name = bone_vis.name = "rig_bone_vis"
                bone_vis.use_fake_user = True
                bpy.context.scene.objects.unlink(bone_vis) # don't want the user deleting this
                bpy.context.scene.objects.active = rig
                bpy.ops.object.mode_set(mode='POSE')
                for bone in rig.pose.bones:
                    bone.custom_shape = bone_vis # apply bone shape
                bpy.ops.object.mode_set(mode='OBJECT') 

class RIG_Export(bpy.types.Operator):
    bl_idname = 'rig.export'
    bl_label = 'Sims 3 Export RIG'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = 'Export Sims 3 RIG files'
    
    filepath = StringProperty(name="File path", description="File filepath used for exporting the RIG file", maxlen=1024, default="")
    filter_folder = BoolProperty(name="Filter folders", description="", default=True, options={'HIDDEN'})
    filter_glob = StringProperty(default="*.grannyrig", options={'HIDDEN'})
    
    def execute(self, context):
        self.parsefile()
        return{'FINISHED'}
        
    def invoke(self, context, event):
        wm = context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def parsefile(self):
        
        def namesToHex(input):
            output = int(input, 16)
            output = struct.pack('l', output)
            return(output)
        
        def namesToHex2(in1, in2):
            o1 = int(in1, 16)
            o2 = int(in2, 16)
            o1 = struct.pack('l', o1)
            o2 = struct.pack('l', o2)
            return(o1, o2)
        
        def nameFix(f, v1, v2):
            nf.write(v1)
            t = f.tell()
            f.seek(t-2)
            f.write(v2)
            t = f.tell()
            f.seek(t-2)
        
        if bpy.context.active_object.type == 'ARMATURE': 
            arm = bpy.context.active_object
            bpy.ops.object.mode_set(mode='EDIT')
            for bone in arm.data.edit_bones:
                if bone.mirrorIndex != repr(arm.data.edit_bones[bone.mirrorBone].boneIndex):
                    bone.mirrorIndex = repr(arm.data.edit_bones[bone.mirrorBone].boneIndex)
                       
            #rename original file
            newfile = self.filepath
            newname = self.filepath + '.bak'
            c = 0
            while True:
                try:
                    os.rename(self.filepath, newname)
                except:
                    newname = newname + repr(c)
                    c += 1
                else:
                    break    
            
            # Open original file and create new file
            with open(newname, 'rb') as f:
                with open(newfile, 'wb') as nf:
                    
                    #get versions from original file
                    for i in range(2):
                        d = struct.unpack('l', f.read(4))[0]
                        nf.write(struct.pack('l', d))
                    
                    #write bone count
                    bones = arm.data.edit_bones 
                    bc = len(bones)
                    nf.write(struct.pack('l', bc))
                    
                    #loop through bones
                    for i in range(len(bones)):
                        if bones[i].parent == None:
                            loc = bones[i].matrix.decompose()[0]
                        else:
                            ploc = bones[i].parent.matrix.decompose()[0]
                            tloc = bones[i].matrix.decompose()[0]                            
                            loc = (tloc[0]-ploc[0], tloc[1]-ploc[1], tloc[2]-ploc[2])
                        #write positions
                        p0,p1,p2 = float(loc[0]), float(loc[1]), float(loc[2])                       
                        nf.write(struct.pack('f', p0))
                        nf.write(struct.pack('f', p1))
                        nf.write(struct.pack('f', p2))
                        
                        #write rotations
                        rot = bones[i].matrix.decompose()[1]
                        r0,r1,r2,r3 = float(rot[0]), float(rot[1]), float(rot[2]), float(rot[3])
                        nf.write(struct.pack('f', r1))
                        nf.write(struct.pack('f', r2))
                        nf.write(struct.pack('f', r3))
                        nf.write(struct.pack('f', r0))
                        
                        #write scaling
                        scl = bones[i].matrix.decompose()[2]
                        s0,s1,s2 = float(scl[0]), float(scl[1]), float(scl[2])
                        nf.write(struct.pack('f', s0))
                        nf.write(struct.pack('f', s1))
                        nf.write(struct.pack('f', s2))
                        
                        #write bone name length
                        nbl = len(bones[i].realName)
                        nf.write(struct.pack('l', nbl))
                        
                        #write bone name
                        name = bones[i].realName
                        print(name)
                        for n in range(nbl):
                            nf.write(struct.pack('1s', name[n].encode('utf-8')))
                           
                        #write mirror index
                        mi = int(bones[i].mirrorIndex)
                        nf.write(struct.pack('l', mi))
                        
                        #write parent index
                        if bones[i].parent == None:
                            pi = -1
                        else:
                            pi = bones[i].parent.boneIndex
                        nf.write(struct.pack('l', pi))
                        
                        #write hash name
                        hn = bones[i].hashName
                        n1, n2 = namesToHex2(hn[4:], hn[:4])
                        nameFix(nf, n1, n2)
                        
                        #write flags
                        fl = namesToHex(bones[i].boneFlags)
                        nf.write(fl)
                    bpy.ops.object.mode_set(mode='POSE')
                    
                    #write rig name length
                    rnl = len(arm.name)
                    nf.write(struct.pack('l', rnl))
                    
                    #write rig name
                    name = arm.name
                    for n in range(rnl):
                        nf.write(struct.pack('1s', name[n].encode('utf-8')))
                        
                    #write 0 ik chains
                    nf.write(struct.pack('l', 0))                        
                                                                                           
def menu_func_import(self, context):
	self.layout.operator(RIG_Import.bl_idname, text="Sims 3 RIG (.grannyrig)")

def menu_func_export(self, context):
	self.layout.operator(RIG_Export.bl_idname, text="Sims 3 RIG (.grannyrig)")
       
def register():
    bpy.utils.register_class(RIG_Import)
    bpy.utils.register_class(RIG_Export)
    bpy.utils.register_class(RIG_Panel)
    bpy.utils.register_class(Add_Bone)
    bpy.utils.register_class(Hash_Names)
    bpy.utils.register_class(Real_Names)
    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.types.INFO_MT_file_export.append(menu_func_export)
def unregister():
    bpy.utils.unregister_class(RIG_Import)
    bpy.utils.unregister_class(RIG_Export)
    bpy.utils.unregister_class(RIG_Panel)
    bpy.utils.unregister_class(Add_Bone)
    bpy.utils.unregister_class(Hash_Names)
    bpy.utils.unregister_class(Real_Names)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    
if __name__ == "__main__":
    register()                