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
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        self.game.update_camera()
        
        # Enable lighting
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # Set up light
        glLightfv(GL_LIGHT0, GL_POSITION, (5, 5, 5, 1))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.8, 0.8, 0.8, 1))
        
        self.render_ground()
        
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
        glColor3f(0.8, 0.8, 0.8)  # Set color for the cat model
        self.game.cat.render()
        glPopMatrix()

        # Render cat's hitbox
        self.render_hitbox(self.game.cat_collider)

        self.game.box.render()
        
        # Render 3D text above the box
        box_position = self.game.box.position
        text_position = [box_position[0], box_position[1] + self.game.box.size[1] / 2 + 1, box_position[2]]  # 1 meter above the box
        glColor3f(1.0, 1.0, 1.0)  # White color for the text
        self.render_3d_text("Box", text_position)

        # Disable lighting for UI rendering
        glDisable(GL_LIGHTING)
        self.render_ui()

    def render_ground(self):
        glBindTexture(GL_TEXTURE_2D, self.game.ground_texture)
        glEnable(GL_TEXTURE_2D)
        
        glBegin(GL_QUADS)
        glColor3f(0.5, 0.5, 0.5)  # Set a gray color for the ground
        glTexCoord2f(0, 0); glVertex3f(-self.game.ground_size, 0, -self.game.ground_size)
        glTexCoord2f(5, 0); glVertex3f(self.game.ground_size, 0, -self.game.ground_size)
        glTexCoord2f(5, 5); glVertex3f(self.game.ground_size, 0, self.game.ground_size)
        glTexCoord2f(0, 5); glVertex3f(-self.game.ground_size, 0, self.game.ground_size)
        glEnd()
        
        glDisable(GL_TEXTURE_2D)

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