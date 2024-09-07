import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from objloader import OBJ
import math
import time
from renderer import Renderer
from box import Box

class Game:
    def __init__(self):
        self.display = (1920, 1080)
        pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Cat Life")
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (self.display[0] / self.display[1]), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        glEnable(GL_DEPTH_TEST)
        
        self.cat = OBJ('models/cat.obj', swapyz=True)
        self.cat_collider = Box([0, 0, 0], [2.0, 2.0, 4.0])  # Doubled size
        self.hitbox_vertical_offset = 0.1  # Add this line to define a small vertical offset
        self.rotation_y = 45
        self.position = [0, -2, 0]
        self.initial_y = self.position[1]
        self.base_speed = 0.1
        self.current_speed = self.base_speed
        self.max_speed = self.base_speed * 3
        self.acceleration_time = 1.0
        self.last_time = pygame.time.get_ticks()
        
        self.ground_texture = self.load_texture('textures/ground.png')
        self.ground_size = 50
        
        self.camera_distance = 20
        self.camera_height = 10
        self.camera_lag = 0.1
        self.camera_position = [0, self.camera_height, self.camera_distance]
        self.camera_rotation = self.rotation_y
        self.is_turning = False
        self.turn_progress = 0
        self.base_turn_speed = 360
        self.current_turn_speed = self.base_turn_speed
        self.max_turn_speed = self.base_turn_speed * 3

        self.jump_height = 4.0
        self.max_jump_height = 8.0
        self.is_jumping = False
        self.jump_start_time = 0
        self.jump_hold_time = 0
        self.max_jump_hold_time = 0.3
        self.jump_velocity = 0
        self.gravity = -9.8 * 4
        self.min_jump_velocity = math.sqrt(2 * abs(self.gravity) * (self.jump_height * 0.25))

        self.clock = pygame.time.Clock()
        self.fps = 60
        self.frame_time = 1.0 / self.fps
        self.current_fps = self.fps

        self.renderer = Renderer(self)

        self.is_flipping = False
        self.flip_progress = 0
        self.flip_height = 6.0
        self.flip_start_y = 0
        self.flip_rotation = 0
        self.flip_duration = 0.8
        self.flip_timer = 0
        self.flip_direction = 1

        self.box = Box([5, 0, 5], [6, 6, 6])

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

    def update_camera(self):
        camera_angle = self.rotation_y
        if self.is_turning:
            camera_angle += self.turn_progress

        ideal_x = self.position[0] - self.camera_distance * math.sin(math.radians(camera_angle))
        ideal_z = self.position[2] - self.camera_distance * math.cos(math.radians(camera_angle))

        self.camera_position[0] += (ideal_x - self.camera_position[0]) * self.camera_lag
        self.camera_position[2] += (ideal_z - self.camera_position[2]) * self.camera_lag

        target_rotation = camera_angle
        rotation_diff = (target_rotation - self.camera_rotation + 180) % 360 - 180
        self.camera_rotation += rotation_diff * self.camera_lag

        glLoadIdentity()
        gluLookAt(
            self.camera_position[0], self.camera_position[1], self.camera_position[2],
            self.position[0], self.position[1], self.position[2],
            0, 1, 0
        )

        # Update cat collider position and rotation
        self.cat_collider.position = [
            self.position[0],
            self.position[1] + self.cat_collider.size[1] / 2 + self.hitbox_vertical_offset,  # Add the offset here
            self.position[2]
        ]
        self.cat_collider.rotation = self.rotation_y

    def run(self):
        previous_time = time.time()
        lag = 0.0

        while True:
            current_time = time.time()
            elapsed_time = current_time - previous_time
            previous_time = current_time
            lag += elapsed_time

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_t and not self.is_turning:
                        self.is_turning = True
                        self.turn_progress = 0

            while lag >= self.frame_time:
                keys = pygame.key.get_pressed()
                self.handle_keys(keys, self.frame_time)
                lag -= self.frame_time

            self.current_fps = self.clock.get_fps()

            self.renderer.render()

            pygame.display.flip()
            self.clock.tick(self.fps)

    def handle_keys(self, keys, dt):
        rotation_speed = 120 * dt

        is_shift_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        target_speed = self.max_speed if is_shift_pressed else self.base_speed
        target_turn_speed = self.max_turn_speed if is_shift_pressed else self.base_turn_speed

        speed_change = (self.max_speed - self.base_speed) * (dt / self.acceleration_time)
        turn_speed_change = (self.max_turn_speed - self.base_turn_speed) * (dt / self.acceleration_time)

        if self.current_speed < target_speed:
            self.current_speed = min(self.current_speed + speed_change, target_speed)
        elif self.current_speed > target_speed:
            self.current_speed = max(self.current_speed - speed_change, target_speed)

        if self.current_turn_speed < target_turn_speed:
            self.current_turn_speed = min(self.current_turn_speed + turn_speed_change, target_turn_speed)
        elif self.current_turn_speed > target_turn_speed:
            self.current_turn_speed = max(self.current_turn_speed - turn_speed_change, target_turn_speed)

        if not self.is_turning:
            if keys[pygame.K_RIGHT]:
                self.rotation_y -= rotation_speed
            if keys[pygame.K_LEFT]:
                self.rotation_y += rotation_speed

            rotation_rad = math.radians(self.rotation_y)

            if keys[pygame.K_UP]:
                new_x = self.position[0] + math.sin(rotation_rad) * self.current_speed * dt * 60
                new_z = self.position[2] + math.cos(rotation_rad) * self.current_speed * dt * 60
                
                # Create a temporary collider at the new position
                temp_collider = Box([new_x, self.position[1] + self.cat_collider.size[1] / 2 + self.hitbox_vertical_offset, new_z], self.cat_collider.size)  # Add the offset here
                temp_collider.rotation = self.rotation_y
                
                # Check for collision with the box
                if not self.box.check_collision(temp_collider):
                    self.position[0] = new_x
                    self.position[2] = new_z
                    self.cat_collider.position = [new_x, self.position[1] + self.cat_collider.size[1] / 2 + self.hitbox_vertical_offset, new_z]  # Add the offset here

        if self.is_turning:
            self.turn_progress += self.current_turn_speed * dt
            if self.turn_progress >= 180:
                self.is_turning = False
                self.rotation_y += 180
                self.turn_progress = 0

        self.rotation_y %= 360

        if not self.is_jumping and not self.is_flipping and keys[pygame.K_SPACE]:
            self.is_jumping = True
            self.jump_start_time = time.time()
            self.jump_hold_time = 0
            self.jump_velocity = self.min_jump_velocity

        if self.is_jumping or (not self.is_flipping and self.position[1] > self.initial_y):
            current_time = time.time()
            if self.is_jumping and keys[pygame.K_SPACE] and current_time - self.jump_start_time < self.max_jump_hold_time:
                self.jump_hold_time = current_time - self.jump_start_time
                jump_progress = min(self.jump_hold_time / self.max_jump_hold_time, 1)
                target_velocity = math.sqrt(2 * abs(self.gravity) * (self.jump_height + (self.max_jump_height - self.jump_height) * jump_progress))
                self.jump_velocity = min(self.jump_velocity + (target_velocity - self.jump_velocity) * dt * 10, target_velocity)
            else:
                self.jump_velocity += self.gravity * dt
            
            new_y = self.position[1] + self.jump_velocity * dt
            new_collider_position = [
                self.position[0],
                new_y + self.cat_collider.size[1] / 2 + self.hitbox_vertical_offset,
                self.position[2]
            ]

            # Check for collision with the box using the cat's new position
            temp_collider = Box(new_collider_position, self.cat_collider.size)
            temp_collider.rotation = self.rotation_y

            if self.box.check_collision(temp_collider):
                # If there's a collision, resolve it
                if self.jump_velocity > 0:  # Moving upwards
                    self.position[1] = self.box.position[1] + self.box.size[1]/2 + self.cat_collider.size[1]/2 + self.hitbox_vertical_offset
                else:  # Moving downwards
                    self.position[1] = self.box.position[1] - self.box.size[1]/2 - self.cat_collider.size[1]/2 - self.hitbox_vertical_offset
                self.is_jumping = False
                self.jump_velocity = 0
            else:
                # If no collision, update the position
                self.position[1] = new_y

            self.cat_collider.position = [
                self.position[0],
                self.position[1] + self.cat_collider.size[1] / 2 + self.hitbox_vertical_offset,
                self.position[2]
            ]

            if self.position[1] <= self.initial_y:
                self.is_jumping = False
                self.position[1] = self.initial_y
                self.cat_collider.position = [
                    self.position[0],
                    self.position[1] + self.cat_collider.size[1] / 2 + self.hitbox_vertical_offset,
                    self.position[2]
                ]
                self.jump_velocity = 0

        if not self.is_jumping and not self.is_flipping:
            if keys[pygame.K_f]:
                self.start_flip(1)
            elif keys[pygame.K_b]:
                self.start_flip(-1)

        if self.is_flipping:
            self.flip_timer += dt
            self.jump_velocity += self.gravity * dt
            self.position[1] += self.jump_velocity * dt

            self.flip_rotation = (self.flip_timer / self.flip_duration) * 360 * self.flip_direction
            self.flip_rotation = max(0, min(abs(self.flip_rotation), 360)) * self.flip_direction

            if self.position[1] <= self.initial_y:
                self.position[1] = self.initial_y
                self.is_flipping = False
                self.flip_rotation = 0
                self.jump_velocity = 0

    def start_flip(self, direction):
        self.is_flipping = True
        self.flip_timer = 0
        self.jump_velocity = math.sqrt(2 * abs(self.gravity) * self.flip_height)
        self.flip_start_y = self.position[1]
        self.flip_direction = direction
        self.flip_rotation = 0
