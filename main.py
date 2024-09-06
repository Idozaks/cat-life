import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from objloader import OBJ
import math

class Game:
    def __init__(self):
        pygame.init()
        self.display = (800, 600)
        pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL)
        
        # Set up the camera for an isometric-like view
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (self.display[0] / self.display[1]), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        glEnable(GL_DEPTH_TEST)
        
        self.cat = OBJ('models/cat.obj', swapyz=True)
        self.rotation_y = 45  # Initial rotation to match camera
        self.position = [0, -2, 0]  # Initial position of the cat
        self.base_speed = 0.1
        self.current_speed = self.base_speed
        self.max_speed = self.base_speed * 3
        self.acceleration_time = 1.0  # Time to reach max speed in seconds
        self.last_time = pygame.time.get_ticks()
        self.font = pygame.font.Font(None, 36)
        self.text_textures = {}
        
        # Add ground plane texture
        self.ground_texture = self.load_texture('textures/ground.png')
        
        # Define ground plane size
        self.ground_size = 50
        
        # Camera settings
        self.camera_distance = 20
        self.camera_height = 10
        self.camera_lag = 0.1  # Adjust this value to change the lag (0 to 1)
        self.camera_position = [0, self.camera_height, self.camera_distance]
        self.camera_rotation = self.rotation_y
        self.is_turning = False
        self.turn_progress = 0
        self.turn_speed = 360  # Degrees per second

    def load_texture(self, filename):
        texture_surface = pygame.image.load(filename)
        texture_data = pygame.image.tostring(texture_surface, "RGBA", 1)
        width = texture_surface.get_width()
        height = texture_surface.get_height()
        
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
        
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        
        return texture_id

    def render_ground(self):
        glBindTexture(GL_TEXTURE_2D, self.ground_texture)
        glEnable(GL_TEXTURE_2D)
        
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(-self.ground_size, -2, -self.ground_size)
        glTexCoord2f(5, 0); glVertex3f(self.ground_size, -2, -self.ground_size)
        glTexCoord2f(5, 5); glVertex3f(self.ground_size, -2, self.ground_size)
        glTexCoord2f(0, 5); glVertex3f(-self.ground_size, -2, self.ground_size)
        glEnd()
        
        glDisable(GL_TEXTURE_2D)

    def update_camera(self):
        # Calculate ideal camera position
        camera_angle = self.rotation_y
        if self.is_turning:
            camera_angle += self.turn_progress

        ideal_x = self.position[0] - self.camera_distance * math.sin(math.radians(camera_angle))
        ideal_z = self.position[2] - self.camera_distance * math.cos(math.radians(camera_angle))

        # Interpolate camera position
        self.camera_position[0] += (ideal_x - self.camera_position[0]) * self.camera_lag
        self.camera_position[2] += (ideal_z - self.camera_position[2]) * self.camera_lag

        # Interpolate camera rotation
        target_rotation = camera_angle
        rotation_diff = (target_rotation - self.camera_rotation + 180) % 360 - 180
        self.camera_rotation += rotation_diff * self.camera_lag

        # Apply camera transform
        glLoadIdentity()
        gluLookAt(
            self.camera_position[0], self.camera_position[1], self.camera_position[2],
            self.position[0], self.position[1], self.position[2],
            0, 1, 0
        )

    def run(self):
        while True:
            current_time = pygame.time.get_ticks()
            dt = (current_time - self.last_time) / 1000.0  # Convert to seconds
            self.last_time = current_time

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_t and not self.is_turning:
                    self.is_turning = True
                    self.turn_progress = 0

            keys = pygame.key.get_pressed()
            self.handle_keys(keys, dt)

            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            # Update and apply camera transform
            self.update_camera()
            
            # Reset color to white before rendering 3D scene
            glColor3f(1.0, 1.0, 1.0)
            
            # Render ground plane
            self.render_ground()
            
            # Render 3D scene
            glPushMatrix()
            glTranslatef(*self.position)
            glRotatef(self.rotation_y, 0, 1, 0)
            if self.is_turning:
                glRotatef(self.turn_progress, 0, 1, 0)
            glRotatef(180, 0, 1, 0)  # Rotate the cat 180 degrees to face the correct direction
            glScalef(0.2, 0.2, 0.2)  # Scale the cat to be smaller
            self.cat.render()
            glPopMatrix()

            # Render UI
            self.render_ui()

            pygame.display.flip()
            pygame.time.wait(10)

    def handle_keys(self, keys, dt):
        rotation_speed = 2

        # Handle acceleration
        target_speed = self.max_speed if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else self.base_speed
        speed_change = (self.max_speed - self.base_speed) * (dt / self.acceleration_time)
        if self.current_speed < target_speed:
            self.current_speed = min(self.current_speed + speed_change, target_speed)
        elif self.current_speed > target_speed:
            self.current_speed = max(self.current_speed - speed_change, target_speed)

        if not self.is_turning:
            if keys[pygame.K_RIGHT]:
                self.rotation_y -= rotation_speed
            if keys[pygame.K_LEFT]:
                self.rotation_y += rotation_speed

            # Convert rotation to radians
            rotation_rad = math.radians(self.rotation_y)

            if keys[pygame.K_UP]:
                # Move forward in the direction the cat is facing
                self.position[0] += math.sin(rotation_rad) * self.current_speed
                self.position[2] += math.cos(rotation_rad) * self.current_speed

        # Handle turning
        if self.is_turning:
            self.turn_progress += self.turn_speed * dt
            if self.turn_progress >= 180:
                self.is_turning = False
                self.rotation_y += 180
                self.turn_progress = 0

        # Ensure rotation stays within 0-360 range
        self.rotation_y %= 360

    def render_ui(self):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.display[0], 0, self.display[1], -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        speed_units = "units/s"
        self.render_text(f"Speed: {self.current_speed:.2f} {speed_units}", (10, self.display[1] - 60))

        acceleration = (self.current_speed - self.base_speed) / (self.max_speed - self.base_speed) * 100
        self.render_text(f"Acceleration: {acceleration:.0f}%", (10, self.display[1] - 100))

        self.render_text(f"Base Speed: {self.base_speed:.2f} {speed_units}", (10, self.display[1] - 140))
        self.render_text(f"Max Speed: {self.max_speed:.2f} {speed_units}", (10, self.display[1] - 180))

        self.render_speedometer()

        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    def render_text(self, text, position):
        if text not in self.text_textures:
            surface = self.font.render(text, True, (255, 255, 255, 255))
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
        glTexCoord2f(0, 1); glVertex2f(position[0], position[1])
        glTexCoord2f(1, 1); glVertex2f(position[0] + width, position[1])
        glTexCoord2f(1, 0); glVertex2f(position[0] + width, position[1] + height)
        glTexCoord2f(0, 0); glVertex2f(position[0], position[1] + height)
        glEnd()
        glDisable(GL_TEXTURE_2D)

    def render_speedometer(self):
        center = (self.display[0] - 100, 150)
        radius = 80
        start_angle = math.pi
        end_angle = 2 * math.pi
        num_segments = 100

        # Draw speedometer background
        glColor3f(0.4, 0.4, 0.4)
        glBegin(GL_LINE_STRIP)
        for i in range(num_segments + 1):
            theta = start_angle + (end_angle - start_angle) * i / num_segments
            glVertex2f(center[0] + radius * math.cos(theta), center[1] + radius * math.sin(theta))
        glEnd()

        # Draw speed indicator
        speed_ratio = (self.current_speed - self.base_speed) / (self.max_speed - self.base_speed)
        speed_angle = start_angle + speed_ratio * (end_angle - start_angle)
        end_pos = (center[0] + radius * math.cos(speed_angle), center[1] + radius * math.sin(speed_angle))
        
        glColor3f(1.0, 0.0, 0.0)
        glBegin(GL_LINES)
        glVertex2f(*center)
        glVertex2f(*end_pos)
        glEnd()

        # Render speedometer labels
        self.render_text(f"{self.base_speed:.1f}", (center[0] - radius - 30, center[1] - 10))
        self.render_text(f"{self.max_speed:.1f}", (center[0] + radius + 10, center[1] - 10))
        self.render_text("Speed", (center[0] - 20, center[1] - radius - 20))

Game().run()