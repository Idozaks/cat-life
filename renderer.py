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
        
        glColor3f(1.0, 1.0, 1.0)
        
        self.render_ground()
        
        glPushMatrix()
        glTranslatef(*self.game.position)
        glRotatef(self.game.rotation_y, 0, 1, 0)
        if self.game.is_turning:
            glRotatef(self.game.turn_progress, 0, 1, 0)
        if self.game.is_flipping:
            glRotatef(self.game.flip_rotation, 1, 0, 0)  # Rotation for flip
        glRotatef(180, 0, 1, 0)
        glScalef(0.2, 0.2, 0.2)
        self.game.cat.render()
        glPopMatrix()

        # Render cat's hitbox
        self.render_hitbox(self.game.cat_collider)

        self.render_ui()

        self.game.box.render()

    def render_ground(self):
        glBindTexture(GL_TEXTURE_2D, self.game.ground_texture)
        glEnable(GL_TEXTURE_2D)
        
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(-self.game.ground_size, -2, -self.game.ground_size)
        glTexCoord2f(5, 0); glVertex3f(self.game.ground_size, -2, -self.game.ground_size)
        glTexCoord2f(5, 5); glVertex3f(self.game.ground_size, -2, self.game.ground_size)
        glTexCoord2f(0, 5); glVertex3f(-self.game.ground_size, -2, self.game.ground_size)
        glEnd()
        
        glDisable(GL_TEXTURE_2D)

    def render_ui(self):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.game.display[0], 0, self.game.display[1], -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.render_text("Cat Life", (20, self.game.display[1] - 40), font_size=48)
        self.render_text(f"FPS: {self.game.current_fps:.1f}", (self.game.display[0] - 150, self.game.display[1] - 40))

        speed_units = "units/s"
        self.render_text(f"Speed: {self.game.current_speed:.2f} {speed_units}", (20, self.game.display[1] - 100))

        acceleration = (self.game.current_speed - self.game.base_speed) / (self.game.max_speed - self.game.base_speed) * 100
        self.render_text(f"Acceleration: {acceleration:.0f}%", (20, self.game.display[1] - 150))

        self.render_text(f"Base Speed: {self.game.base_speed:.2f} {speed_units}", (20, self.game.display[1] - 200))
        self.render_text(f"Max Speed: {self.game.max_speed:.2f} {speed_units}", (20, self.game.display[1] - 250))

        self.render_speedometer()

        self.render_text("Controls:", (20, self.game.display[1] - 300))
        self.render_text("Arrow Up: Move forward", (20, self.game.display[1] - 340))
        self.render_text("Arrow Left/Right: Rotate", (20, self.game.display[1] - 380))
        self.render_text("T: Turn 180 degrees", (20, self.game.display[1] - 420))
        self.render_text("Shift: Accelerate", (20, self.game.display[1] - 460))
        self.render_text("Space: Jump", (20, self.game.display[1] - 500))
        self.render_text("F: Front Flip", (20, self.game.display[1] - 540))
        self.render_text("B: Backflip", (20, self.game.display[1] - 580))

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