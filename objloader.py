import pygame
from OpenGL.GL import *
import os

class MTL(object):
    def __init__(self, filename):
        self.contents = {}
        mtl = None
        self.filename = filename
        for line in open(filename, "r"):
            if line.startswith('#'): continue
            values = line.split()
            if not values: continue
            if values[0] == 'newmtl':
                mtl = self.contents[values[1]] = {}
            elif mtl is None:
                raise ValueError("MTL file doesn't start with newmtl stmt")
            elif values[0] in ['map_Kd', 'map_Ka', 'map_Ks']:
                # These are texture maps, store as strings
                mtl[values[0]] = values[1]
            else:
                try:
                    mtl[values[0]] = list(map(float, values[1:]))
                except ValueError:
                    # If conversion to float fails, store as string
                    mtl[values[0]] = " ".join(values[1:])

    def load_texture(self, filename):
        # Construct the full path to the texture file
        dir_path = os.path.dirname(self.filename)  # Get directory of the .mtl file
        full_path = os.path.join(dir_path, filename)
        
        surf = pygame.image.load(full_path)
        tex_surface = pygame.image.tostring(surf, 'RGBA', 1)
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surf.get_width(), surf.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, tex_surface)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        return tex_id

class OBJ:
    def __init__(self, filename, swapyz=False):
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        self.mtl = None

        material = None
        for line in open(filename, "r"):
            if line.startswith('#'): continue
            values = line.split()
            if not values: continue
            if values[0] == 'v':
                v = list(map(float, values[1:4]))
                if swapyz:
                    v = v[0], v[2], v[1]
                self.vertices.append(v)
            elif values[0] == 'vn':
                v = list(map(float, values[1:4]))
                if swapyz:
                    v = v[0], v[2], v[1]
                self.normals.append(v)
            elif values[0] == 'vt':
                self.texcoords.append(list(map(float, values[1:3])))
            elif values[0] in ('usemtl', 'usemat'):
                material = values[1]
            elif values[0] == 'mtllib':
                self.mtl = MTL(values[1])
            elif values[0] == 'f':
                face = []
                texcoords = []
                norms = []
                for v in values[1:]:
                    w = v.split('/')
                    face.append(int(w[0]))
                    if len(w) >= 2 and len(w[1]) > 0:
                        texcoords.append(int(w[1]))
                    else:
                        texcoords.append(0)
                    if len(w) >= 3 and len(w[2]) > 0:
                        norms.append(int(w[2]))
                    else:
                        norms.append(0)
                self.faces.append((face, norms, texcoords, material))

        self.gl_list = glGenLists(1)
        glNewList(self.gl_list, GL_COMPILE)
        glEnable(GL_TEXTURE_2D)
        glFrontFace(GL_CCW)
        for face in self.faces:
            vertices, normals, texture_coords, material = face

            if material:
                mtl = self.mtl.contents[material]
                if 'map_Kd' in mtl:
                    # Load the texture if it hasn't been loaded yet
                    if isinstance(mtl['map_Kd'], str):
                        mtl['map_Kd'] = self.mtl.load_texture(mtl['map_Kd'])
                    glBindTexture(GL_TEXTURE_2D, mtl['map_Kd'])
                elif 'Kd' in mtl:
                    glColor(*mtl['Kd'])

            glBegin(GL_POLYGON)
            for i in range(len(vertices)):
                if normals[i] > 0:
                    glNormal3fv(self.normals[normals[i] - 1])
                if texture_coords[i] > 0:
                    glTexCoord2fv(self.texcoords[texture_coords[i] - 1])
                glVertex3fv(self.vertices[vertices[i] - 1])
            glEnd()
        glDisable(GL_TEXTURE_2D)
        glEndList()

    def render(self):
        glCallList(self.gl_list)