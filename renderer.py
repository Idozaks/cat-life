import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
import math

class Renderer:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.Font(None, 36)
        self.text_textures = {}

    def render(self):
        glClearColor(0.5, 0.7, 1.0, 1.0)  # Set a light blue background color
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        
        self.game.update_camera()
        
        # Enable fog to create a fade-out effect
        glEnable(GL_FOG)
        glFogfv(GL_FOG_COLOR, (0.5, 0.7, 1.0, 1.0))  # Match fog color with background
        glFogf(GL_FOG_START, 10.0)  # Start fog at 10 units away
        glFogf(GL_FOG_END, 20.0)    # Full fog at 20 units away
        glFogi(GL_FOG_MODE, GL_LINEAR)
        
        # Render skybox or background
        self.render_skybox()
        
        # Render ground
        self.render_ground()
        
        # Render opaque objects
        self.render_cat()
        self.render_hitbox(self.game.cat_collider)
        self.game.box.render()
        
        # Render 3D text above the box
        box_position = self.game.box.position
        text_position = [box_position[0], box_position[1] + self.game.box.size[1] / 2 + 1, box_position[2]]
        glColor3f(1.0, 1.0, 1.0)
        self.render_3d_text("Box", text_position)
        
        # Disable fog for UI rendering
        glDisable(GL_FOG)
        
        # Render UI
        self.render_ui()

    def render_skybox(self):
        glDisable(GL_DEPTH_TEST)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(-1, 1, -1, 1, -1, 1)
        
        glBegin(GL_QUADS)
        glColor3f(0.5, 0.7, 1.0)  # Light blue color
        glVertex3f(-1, -1, -0.999)
        glVertex3f( 1, -1, -0.999)
        glVertex3f( 1,  1, -0.999)
        glVertex3f(-1,  1, -0.999)
        glEnd()
        
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glEnable(GL_DEPTH_TEST)

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
        glTexCoord2f(0, 5); glVertex3f(-self.game.ground_size, 0, self.game.ground_size)
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

    def render_ui(self):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.game.display[0], self.game.display[1], 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.render_text("Cat Life", (20, 40), font_size=48)
        self.render_text(f"FPS: {self.game.current_fps:.1f}", (self.game.display[0] - 150, 40))

        speed_units = "units/s"
        self.render_text(f"Speed: {self.game.current_speed:.2f} {speed_units}", (20, 100))

        acceleration = (self.game.current_speed - self.game.base_speed) / (self.game.max_speed - self.game.base_speed) * 100
        self.render_text(f"Acceleration: {acceleration:.0f}%", (20, 150))

        self.render_text(f"Base Speed: {self.game.base_speed:.2f} {speed_units}", (20, 200))
        self.render_text(f"Max Speed: {self.game.max_speed:.2f} {speed_units}", (20, 250))

        self.render_speedometer()

        self.render_text("Controls:", (20, 300))
        self.render_text("W / Arrow Up: Move forward", (20, 340))
        self.render_text("A/D / Arrow Left/Right: Rotate", (20, 380))
        self.render_text("T: Turn 180 degrees", (20, 420))
        self.render_text("Shift: Accelerate", (20, 460))
        self.render_text("Space: Jump", (20, 500))
        self.render_text("F: Front Flip", (20, 540))
        self.render_text("B: Backflip", (20, 580))

        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    def render_text(self, text, position, font_size=36):
        font = pygame.font.Font(None, font_size)
        if text not in self.text_textures:
            surface = font.render(text, True, (255, 255, 255, 255))
            texture = pygame.image.tostring(surface, 'RGBA', True)
            texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(), surface.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, texture)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            self.text_textures[text] = (texture_id, surface.get_width(), surface.get_height())

        texture_id, width, height = self.text_textures[text]
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glEnable(GL_TEXTURE_2D)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(position[0], position[1])
        glTexCoord2f(1, 0); glVertex2f(position[0] + width, position[1])
        glTexCoord2f(1, 1); glVertex2f(position[0] + width, position[1] + height)
        glTexCoord2f(0, 1); glVertex2f(position[0], position[1] + height)
        glEnd()
        glDisable(GL_TEXTURE_2D)

    def render_speedometer(self):
        center = (self.game.display[0] - 150, 200)
        radius = 100
        start_angle = math.pi
        end_angle = 2 * math.pi
        num_segments = 100

        glColor3f(0.4, 0.4, 0.4)
        glBegin(GL_LINE_STRIP)
        for i in range(num_segments + 1):
            theta = start_angle + (end_angle - start_angle) * i / num_segments
            glVertex2f(center[0] + radius * math.cos(theta), center[1] + radius * math.sin(theta))
        glEnd()

        speed_ratio = (self.game.current_speed - self.game.base_speed) / (self.game.max_speed - self.game.base_speed)
        speed_angle = start_angle + speed_ratio * (end_angle - start_angle)
        end_pos = (center[0] + radius * math.cos(speed_angle), center[1] + radius * math.sin(speed_angle))
        
        glColor3f(1.0, 0.0, 0.0)
        glBegin(GL_LINES)
        glVertex2f(*center)
        glVertex2f(*end_pos)
        glEnd()

        self.render_text(f"{self.game.base_speed:.1f}", (center[0] - radius - 30, center[1] - 10))
        self.render_text(f"{self.game.max_speed:.1f}", (center[0] + radius + 10, center[1] - 10))
        self.render_text("Speed", (center[0] - 20, center[1] - radius - 20))

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

    def render_3d_text(self, text, position):
        glPushMatrix()
        glTranslatef(*position)
        
        # Make text always face the camera
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        glLoadIdentity()
        gluLookAt(modelview[2][0], modelview[2][1], modelview[2][2], 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
        
        # Render text as a 2D overlay
        glDisable(GL_DEPTH_TEST)
        glColor3f(1.0, 1.0, 1.0)  # White color for the text
        
        # Create a surface with the text
        text_surface = self.font.render(text, True, (255, 255, 255, 255))
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        
        # Generate a new texture
        text_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, text_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, text_surface.get_width(), text_surface.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, text_texture)
        
        # Draw a quad with the text texture
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(-0.5, -0.5, 0)
        glTexCoord2f(1, 0); glVertex3f(0.5, -0.5, 0)
        glTexCoord2f(1, 1); glVertex3f(0.5, 0.5, 0)
        glTexCoord2f(0, 1); glVertex3f(-0.5, 0.5, 0)
        glEnd()
        
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)
        
        glPopMatrix()

    def render_sphere(self, radius):
        slices = 16
        stacks = 16
        
        for i in range(stacks):
            lat0 = math.pi * (-0.5 + float(i) / stacks)
            z0 = math.sin(lat0)
            zr0 = math.cos(lat0)
            
            lat1 = math.pi * (-0.5 + float(i+1) / stacks)
            z1 = math.sin(lat1)
            zr1 = math.cos(lat1)
            
            glBegin(GL_QUAD_STRIP)
            for j in range(slices + 1):
                lng = 2 * math.pi * float(j) / slices
                x = math.cos(lng)
                y = math.sin(lng)
                
                glNormal3f(x * zr0, y * zr0, z0)
                glVertex3f(x * zr0 * radius, y * zr0 * radius, z0 * radius)
                glNormal3f(x * zr1, y * zr1, z1)
                glVertex3f(x * zr1 * radius, y * zr1 * radius, z1 * radius)
            glEnd()