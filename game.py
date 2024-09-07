import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from objloader import OBJ
import math
import time
from renderer import Renderer
from box import Box
from jump_mechanics import JumpMechanics
from camera import Camera

class Game:
    def __init__(self):
        self.display = (1920, 1080)
        pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Cat Life")
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (self.display[0] / self.display[1]), 0.1, 200.0)  # Increased far clipping plane to 200.0
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        glEnable(GL_DEPTH_TEST)
        
        self.cat = OBJ('models/cat.obj', swapyz=True)
        self.cat_height = 0.25  # Cat height in meters
        self.cat_length = 0.45  # Typical cat length in meters
        self.cat_width = 0.20   # Typical cat width in meters
        
        self.cat_collider = Box([0, 0, 0], [self.cat_width, self.cat_height, self.cat_length])
        self.hitbox_vertical_offset = 0.05  # 5 cm offset
        
        self.rotation_y = 45
        self.position = [0, self.cat_height / 2, 0]  # Start with cat's feet on the ground
        self.initial_y = self.position[1]
        self.base_speed = 2.0  # Doubled from 1.0 to 2.0 m/s
        self.current_speed = self.base_speed
        self.max_speed = self.base_speed * 3  # Now 6.0 m/s (doubled from previous max of 3.0 m/s)
        
        self.base_turn_speed = 2  # Increase this value for faster base turning
        self.max_turn_speed = self.base_turn_speed * 3  # Adjusted to be 3 times the base turn speed
        self.current_turn_speed = self.base_turn_speed

        self.acceleration_time = 1.0
        self.last_time = pygame.time.get_ticks()
        
        self.ground_texture = self.load_texture('textures/ground.png')
        self.ground_size = 20  # 20 meters square ground
        
        self.camera_height = 2.0  # Increased from 1.5 to 2.0 meters
        self.camera_distance = 4  # Increased from 3 to 4 meters behind the cat
        
        initial_position = (0, 0, 0)  # Adjust as needed
        initial_target = (0, 0, 0)    # Adjust as needed
        initial_distance = 10.0       # Double the original distance
        sensitivity = 0.1             # Adjust as needed
        
        self.camera = Camera(initial_position, initial_target, initial_distance, sensitivity)

        self.jump_height = 1.0  # 1 meter jump height
        self.max_jump_height = 1.5  # 1.5 meters max jump height
        self.gravity = -9.8  # Real-world gravity in m/s^2

        self.clock = pygame.time.Clock()
        self.fps = 60
        self.frame_time = 1.0 / self.fps
        self.current_fps = self.fps

        self.renderer = Renderer(self)

        self.is_turning = False
        self.turn_progress = 0
        self.max_turn_speed = self.base_speed * 3  # Add this line
        self.current_turn_speed = self.base_speed  # Add this line

        self.is_flipping = False
        self.flip_progress = 0
        self.flip_height = 6.0
        self.flip_start_y = 0
        self.flip_rotation = 0
        self.flip_duration = 0.8
        self.flip_timer = 0
        self.flip_direction = 1

        self.box = Box([2, self.cat_height, 2], [1, 1, 1])  # Box 2 meters away, 1 meter cube

        self.jump_mechanics = JumpMechanics(
            initial_y=self.initial_y,
            gravity=self.gravity,
            jump_height=self.jump_height,
            max_jump_height=self.max_jump_height,
            max_jump_hold_time=0.3
        )

        # Set mouse to the center of the screen and hide it
        pygame.mouse.set_pos(self.display[0] // 2, self.display[1] // 2)
        pygame.mouse.set_visible(False)

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
        self.camera.update(self.position, self.cat_collider)

        # Update cat collider position and rotation
        self.cat_collider.position = [
            self.position[0],
            self.position[1] + self.cat_collider.size[1] / 2 + self.hitbox_vertical_offset,
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
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event)
                elif event.type == pygame.MOUSEWHEEL:
                    self.handle_mouse_scroll(event)

            while lag >= self.frame_time:
                keys = pygame.key.get_pressed()
                self.handle_keys(keys, self.frame_time)
                lag -= self.frame_time

            self.current_fps = self.clock.get_fps()

            self.renderer.render()

            pygame.display.flip()
            self.clock.tick(self.fps)

    def handle_mouse_motion(self, event):
        dx, dy = event.rel
        self.camera.handle_mouse_motion(dx, dy)
        
        # Reset mouse position to center
        pygame.mouse.set_pos(self.display[0] // 2, self.display[1] // 2)

    def handle_mouse_scroll(self, event):
        self.camera.handle_mouse_scroll(event.y)

    def handle_keys(self, keys, dt):
        rotation_speed = 120 * dt

        is_shift_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        target_speed = self.max_speed if is_shift_pressed else self.base_speed

        speed_change = (self.max_speed - self.base_speed) * (dt / self.acceleration_time)

        if self.current_speed < target_speed:
            self.current_speed = min(self.current_speed + speed_change, target_speed)
        elif self.current_speed > target_speed:
            self.current_speed = max(self.current_speed - speed_change, target_speed)

        if not self.is_turning:
            # Constant turning
            turn_amount = 2  # Adjust this value to change the turn rate
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.rotation_y -= turn_amount
            elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.rotation_y += turn_amount

            # Gradually return to camera rotation when not turning
            if not (keys[pygame.K_RIGHT] or keys[pygame.K_d] or keys[pygame.K_LEFT] or keys[pygame.K_a]):
                camera_rotation = self.camera.get_rotation()
                rotation_diff = (camera_rotation - self.rotation_y + 180) % 360 - 180
                if abs(rotation_diff) > 1:
                    self.rotation_y += rotation_diff * 0.1  # Adjust this value to change the speed of returning to camera rotation

            rotation_rad = math.radians(self.rotation_y)

            if keys[pygame.K_UP] or keys[pygame.K_w]:
                new_x = self.position[0] - math.sin(rotation_rad) * self.current_speed * dt
                new_z = self.position[2] - math.cos(rotation_rad) * self.current_speed * dt
                
                # Create a temporary collider at the new position
                temp_collider = Box([new_x, self.position[1] + self.cat_collider.size[1] / 2 + self.hitbox_vertical_offset, new_z], self.cat_collider.size)
                temp_collider.rotation = self.rotation_y
                
                # Check for collision with the box
                if not self.box.check_collision(temp_collider):
                    self.position[0] = new_x
                    self.position[2] = new_z
                    self.cat_collider.position = [new_x, self.position[1] + self.cat_collider.size[1] / 2 + self.hitbox_vertical_offset, new_z]

        if self.is_turning:
            self.turn_progress += self.current_turn_speed * dt
            if self.turn_progress >= 180:
                self.is_turning = False
                self.rotation_y += 180
                self.turn_progress = 0

        self.rotation_y %= 360

        if keys[pygame.K_SPACE] and not self.is_flipping:
            self.jump_mechanics.start_jump()

        if self.jump_mechanics.is_jumping or self.is_flipping or self.position[1] > self.initial_y:
            jump_delta = self.jump_mechanics.update_jump(keys, dt, pygame.K_SPACE)
            new_y = self.position[1] + jump_delta
            new_collider_position = [
                self.position[0],
                new_y + self.cat_collider.size[1] / 2 + self.hitbox_vertical_offset,
                self.position[2]
            ]

            temp_collider = Box(new_collider_position, self.cat_collider.size)
            temp_collider.rotation = self.rotation_y

            collision, collision_point = self.check_collision_with_top(temp_collider, self.box)
            if collision and self.jump_mechanics.jump_velocity < 0:
                self.position[1] = collision_point[1] - self.cat_collider.size[1] / 2 - self.hitbox_vertical_offset
                self.jump_mechanics.land()
            else:
                self.position[1] = new_y

            self.cat_collider.position = [
                self.position[0],
                self.position[1] + self.cat_collider.size[1] / 2 + self.hitbox_vertical_offset,
                self.position[2]
            ]

            if self.position[1] <= self.initial_y:
                self.position[1] = self.initial_y
                self.cat_collider.position = [
                    self.position[0],
                    self.position[1] + self.cat_collider.size[1] / 2 + self.hitbox_vertical_offset,
                    self.position[2]
                ]
                self.jump_mechanics.land()

        if not self.jump_mechanics.is_jumping and not self.is_flipping:
            if keys[pygame.K_f]:
                self.start_flip(1)
            elif keys[pygame.K_b]:
                self.start_flip(-1)

        if self.is_flipping:
            self.flip_timer += dt
            self.jump_mechanics.jump_velocity += self.gravity * dt
            self.position[1] += self.jump_mechanics.jump_velocity * dt

            self.flip_rotation = (self.flip_timer / self.flip_duration) * 360 * self.flip_direction
            self.flip_rotation = max(0, min(abs(self.flip_rotation), 360)) * self.flip_direction

            if self.position[1] <= self.initial_y:
                self.position[1] = self.initial_y
                self.is_flipping = False
                self.flip_rotation = 0
                self.jump_mechanics.jump_velocity = 0

    def start_flip(self, direction):
        self.is_flipping = True
        self.flip_timer = 0
        self.jump_mechanics.jump_velocity = math.sqrt(2 * abs(self.gravity) * self.flip_height)
        self.flip_start_y = self.position[1]
        self.flip_direction = direction
        self.flip_rotation = 0

    def check_collision_with_top(self, cat_collider, box):
        # Check if the cat's bottom is above the box's top
        cat_bottom = cat_collider.position[1] - cat_collider.size[1] / 2
        box_top = box.position[1] + box.size[1] / 2

        if cat_bottom > box_top:
            return False, None

        # Check if the cat's horizontal position overlaps with the box
        cat_left = cat_collider.position[0] - cat_collider.size[0] / 2
        cat_right = cat_collider.position[0] + cat_collider.size[0] / 2
        cat_front = cat_collider.position[2] - cat_collider.size[2] / 2
        cat_back = cat_collider.position[2] + cat_collider.size[2] / 2

        box_left = box.position[0] - box.size[0] / 2
        box_right = box.position[0] + box.size[0] / 2
        box_front = box.position[2] - box.size[2] / 2
        box_back = box.position[2] + box.size[2] / 2

        if (cat_left < box_right and cat_right > box_left and
            cat_front < box_back and cat_back > box_front):
            # Calculate the collision point (use the center of the overlapping area)
            collision_x = (max(cat_left, box_left) + min(cat_right, box_right)) / 2
            collision_z = (max(cat_front, box_front) + min(cat_back, box_back)) / 2
            return True, (collision_x, box_top, collision_z)

        return False, None
