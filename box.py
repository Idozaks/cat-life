from OpenGL.GL import *

import math

class Box:
    def __init__(self, position, size):
        self.position = position
        self.size = size
        self.rotation = 0  # Add this line

    def render(self):
        glPushMatrix()
        glTranslatef(*self.position)
        glScalef(*self.size)
        
        glBegin(GL_QUADS)
        # Front face
        glColor3f(1.0, 0.7, 0.3)  # Brighter orange color
        glVertex3f(-0.5, -0.5,  0.5)
        glVertex3f( 0.5, -0.5,  0.5)
        glVertex3f( 0.5,  0.5,  0.5)
        glVertex3f(-0.5,  0.5,  0.5)
        # Back face
        glVertex3f(-0.5, -0.5, -0.5)
        glVertex3f(-0.5,  0.5, -0.5)
        glVertex3f( 0.5,  0.5, -0.5)
        glVertex3f( 0.5, -0.5, -0.5)
        # Top face
        glColor3f(1.0, 0.8, 0.4)  # Slightly lighter for the top
        glVertex3f(-0.5,  0.5, -0.5)
        glVertex3f(-0.5,  0.5,  0.5)
        glVertex3f( 0.5,  0.5,  0.5)
        glVertex3f( 0.5,  0.5, -0.5)
        # Bottom face
        glVertex3f(-0.5, -0.5, -0.5)
        glVertex3f( 0.5, -0.5, -0.5)
        glVertex3f( 0.5, -0.5,  0.5)
        glVertex3f(-0.5, -0.5,  0.5)
        # Right face
        glColor3f(0.9, 0.6, 0.2)  # Slightly darker for sides
        glVertex3f( 0.5, -0.5, -0.5)
        glVertex3f( 0.5,  0.5, -0.5)
        glVertex3f( 0.5,  0.5,  0.5)
        glVertex3f( 0.5, -0.5,  0.5)
        # Left face
        glVertex3f(-0.5, -0.5, -0.5)
        glVertex3f(-0.5, -0.5,  0.5)
        glVertex3f(-0.5,  0.5,  0.5)
        glVertex3f(-0.5,  0.5, -0.5)
        glEnd()
        
        glPopMatrix()

    def check_collision(self, other):
        if isinstance(other, Box):
            # Perform rotated box collision check
            return self.check_rotated_box_collision(other)
        else:  # Assume it's a position list
            # Perform point-box collision check
            return self.check_point_collision(other)

    def check_rotated_box_collision(self, other):
        # Simplified collision check for rotated boxes
        # This is an approximation and may not be 100% accurate for all rotations
        
        # Calculate the axes of both boxes
        axes = [
            self.get_axis(0), self.get_axis(1), self.get_axis(2),
            other.get_axis(0), other.get_axis(1), other.get_axis(2)
        ]
        
        # Check for separation along each axis
        for axis in axes:
            if self.is_separated_along_axis(other, axis):
                return False
        
        return True

    def get_axis(self, index):
        angle = math.radians(self.rotation)
        if index == 0:
            return [math.cos(angle), 0, -math.sin(angle)]
        elif index == 1:
            return [0, 1, 0]
        else:
            return [math.sin(angle), 0, math.cos(angle)]

    def is_separated_along_axis(self, other, axis):
        proj1 = self.project_onto_axis(axis)
        proj2 = other.project_onto_axis(axis)
        return proj1[1] < proj2[0] or proj2[1] < proj1[0]

    def project_onto_axis(self, axis):
        vertices = self.get_vertices()
        min_proj = max_proj = self.dot_product(vertices[0], axis)
        for i in range(1, 8):
            proj = self.dot_product(vertices[i], axis)
            min_proj = min(min_proj, proj)
            max_proj = max(max_proj, proj)
        return [min_proj, max_proj]

    def get_vertices(self):
        angle = math.radians(self.rotation)
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)
        
        vertices = []
        for x in (-1, 1):
            for y in (-1, 1):
                for z in (-1, 1):
                    rotated_x = x * cos_angle - z * sin_angle
                    rotated_z = x * sin_angle + z * cos_angle
                    vertices.append([
                        self.position[0] + rotated_x * self.size[0]/2,
                        self.position[1] + y * self.size[1]/2,
                        self.position[2] + rotated_z * self.size[2]/2
                    ])
        return vertices

    def dot_product(self, v1, v2):
        return sum(a * b for a, b in zip(v1, v2))

    def check_point_collision(self, point):
        # Transform the point to the box's local space
        local_point = self.to_local_space(point)
        
        # Check if the local point is inside the box
        return (
            abs(local_point[0]) <= self.size[0]/2 and
            abs(local_point[1]) <= self.size[1]/2 and
            abs(local_point[2]) <= self.size[2]/2
        )

    def to_local_space(self, point):
        dx = point[0] - self.position[0]
        dy = point[1] - self.position[1]
        dz = point[2] - self.position[2]
        
        angle = math.radians(self.rotation)
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)
        
        local_x = dx * cos_angle + dz * sin_angle
        local_y = dy
        local_z = -dx * sin_angle + dz * cos_angle
        
        return [local_x, local_y, local_z]