import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
import math

class Renderer:
    def __init__(self, game):
        self.game = game

    def render(self):
        glClearColor(0.5, 0.7, 1.0, 1.0)  # Set a light blue background color
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        
        self.game.update_camera()
        
        # Render ground
        self.render_ground()
        
        # Render opaque objects
        self.render_cat()
        self.render_hitbox(self.game.cat_collider)
        self.game.box.render()

    def render_ground(self):
        glPushMatrix()
        glTranslatef(0, -0.01, 0)  # Move the ground slightly below 0 to avoid z-fighting
        
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.game.ground_texture)
        
        glBegin(GL_QUADS)
        glColor3f(1.0, 1.0, 1.0)  # Set color to white to show texture properly
        glTexCoord2f(0, 0); glVertex3f(-self.game.ground_size, 0, -self.game.ground_size)
        glTexCoord2f(5, 0); glVertex3f(self.game.ground_size, 0, -self.game.ground_size)
        glTexCoord2f(5, 5); glVertex3f(self.game.ground_size, 0, self.game.ground_size)
        glTexCoord2f(0, 5); glVertex3f(-self.game.ground_size, 0, self.game.ground_size)  # Fixed this line
        glEnd()
        
        glDisable(GL_TEXTURE_2D)
        glPopMatrix()

    def render_cat(self):
        glPushMatrix()
        glTranslatef(*self.game.position)
        glRotatef(self.game.rotation_y, 0, 1, 0)
        if self.game.is_turning:
            glRotatef(self.game.turn_progress, 0, 1, 0)
        if self.game.is_flipping:
            glRotatef(self.game.flip_rotation, 1, 0, 0)  # Rotation for flip
        glRotatef(0, 0, 1, 0)
        scale_factor = self.game.cat_height / 5  # Assuming the model is 5 units tall
        glScalef(scale_factor, scale_factor, scale_factor)
        glColor3f(1.0, 0.7, 0.3)  # Set a brighter color for the cat model
        self.game.cat.render()
        glPopMatrix()

    def render_hitbox(self, box):
        glPushMatrix()
        glTranslatef(*box.position)
        glRotatef(box.rotation, 0, 1, 0)  # Apply rotation around Y-axis
        
        # Change the color to bright magenta with some transparency
        glColor4f(1.0, 0.0, 1.0, 0.5)  # Bright magenta with 50% opacity
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        glBegin(GL_LINES)
        
        # Draw the hitbox
        for x in (-1, 1):
            for y in (-1, 1):
                for z in (-1, 1):
                    glVertex3f(x * box.size[0]/2, y * box.size[1]/2, z * box.size[2]/2)
                    glVertex3f(x * box.size[0]/2, y * box.size[1]/2, -z * box.size[2]/2)
                    glVertex3f(x * box.size[0]/2, y * box.size[1]/2, z * box.size[2]/2)
                    glVertex3f(x * box.size[0]/2, -y * box.size[1]/2, z * box.size[2]/2)
                    glVertex3f(x * box.size[0]/2, y * box.size[1]/2, z * box.size[2]/2)
                    glVertex3f(-x * box.size[0]/2, y * box.size[1]/2, z * box.size[2]/2)
        
        glEnd()
        
        glDisable(GL_BLEND)
        glPopMatrix()