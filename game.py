import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import time
from renderer import Renderer
from box import Box
from camera import Camera
from cat import Cat  # Import the new Cat class

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
        
        self.gravity = -9.8  # Real-world gravity in m/s^2
        cat_initial_height = 0.25 / 2  # Half of the cat's height
        self.cat = Cat([0, cat_initial_height, 0], self.gravity)  # Create Cat instance
        
        self.ground_texture = self.load_texture('textures/ground.png')
        self.ground_size = 20  # 20 meters square ground
        
        self.camera_height = 2.0  # Increased from 1.5 to 2.0 meters
        self.camera_distance = 4  # Increased from 3 to 4 meters behind the cat
        
        initial_position = (0, 0, 0)  # Adjust as needed
        initial_target = (0, 0, 0)    # Adjust as needed
        initial_distance = 10.0       # Double the original distance
        sensitivity = 0.1             # Adjust as needed
        
        self.camera = Camera(initial_position, initial_target, initial_distance, sensitivity)

        self.clock = pygame.time.Clock()
        self.fps = 60
        self.frame_time = 1.0 / self.fps
        self.current_fps = self.fps

        self.renderer = Renderer(self)

        self.box = Box([2, self.cat.height, 2], [1, 1, 1])  # Box 2 meters away, 1 meter cube

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
        current_time = time.time()
        self.camera.update(self.cat.position, self.cat.collider, current_time)
        self.cat.update_collider()

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
                    if event.key == pygame.K_t and not self.cat.is_turning:
                        self.cat.is_turning = True
                        self.cat.turn_progress = 0
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event)
                elif event.type == pygame.MOUSEWHEEL:
                    self.handle_mouse_scroll(event)

            while lag >= self.frame_time:
                keys = pygame.key.get_pressed()
                self.handle_keys(keys, self.frame_time)
                self.update_camera()  # Make sure to call this every frame
                lag -= self.frame_time

            self.current_fps = self.clock.get_fps()

            self.renderer.render()

            pygame.display.flip()
            self.clock.tick(self.fps)

    def handle_mouse_motion(self, event):
        dx, dy = event.rel
        current_time = time.time()
        self.camera.handle_mouse_motion(dx, dy, current_time)
        
        # Reset mouse position to center
        pygame.mouse.set_pos(self.display[0] // 2, self.display[1] // 2)

    def handle_mouse_scroll(self, event):
        self.camera.handle_mouse_scroll(event.y)

    def handle_keys(self, keys, dt):
        rotation_speed = 120 * dt

        is_shift_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        target_speed = self.cat.max_speed if is_shift_pressed else self.cat.base_speed

        speed_change = (self.cat.max_speed - self.cat.base_speed) * (dt / self.cat.acceleration_time)

        if self.cat.current_speed < target_speed:
            self.cat.current_speed = min(self.cat.current_speed + speed_change, target_speed)
        elif self.cat.current_speed > target_speed:
            self.cat.current_speed = max(self.cat.current_speed - speed_change, target_speed)

        if not self.cat.is_turning:
            # Constant turning
            turn_amount = 2  # Adjust this value to change the turn rate
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.cat.rotation_y -= turn_amount
                self.camera.rotate_horizontal(-turn_amount)  # Set target rotation for camera
            elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.cat.rotation_y += turn_amount
                self.camera.rotate_horizontal(turn_amount)  # Set target rotation for camera

            # Remove the gradual return to camera rotation
            # This section is no longer needed as the camera will always match the cat's rotation

            rotation_rad = math.radians(self.cat.rotation_y)

            if keys[pygame.K_UP] or keys[pygame.K_w]:
                new_x = self.cat.position[0] - math.sin(rotation_rad) * self.cat.current_speed * dt
                new_z = self.cat.position[2] - math.cos(rotation_rad) * self.cat.current_speed * dt
                
                # Create a temporary collider at the new position
                temp_collider = Box([new_x, self.cat.position[1] + self.cat.collider.size[1] / 2 + self.cat.hitbox_vertical_offset, new_z], self.cat.collider.size)
                temp_collider.rotation = self.cat.rotation_y
                
                # Check for collision with the box
                if not self.box.check_collision(temp_collider):
                    self.cat.position[0] = new_x
                    self.cat.position[2] = new_z
                    self.cat.collider.position = [new_x, self.cat.position[1] + self.cat.collider.size[1] / 2 + self.cat.hitbox_vertical_offset, new_z]

        if self.cat.is_turning:
            self.cat.turn_progress += self.cat.current_turn_speed * dt
            if self.cat.turn_progress >= 180:
                self.cat.is_turning = False
                self.cat.rotation_y += 180
                self.cat.turn_progress = 0

        self.cat.rotation_y %= 360

        if keys[pygame.K_SPACE] and not self.cat.is_flipping:
            self.cat.jump_mechanics.start_jump()

        if self.cat.jump_mechanics.is_jumping or self.cat.is_flipping or self.cat.position[1] > self.cat.initial_y:
            jump_delta = self.cat.jump_mechanics.update_jump(keys, dt, pygame.K_SPACE)
            new_y = self.cat.position[1] + jump_delta
            new_collider_position = [
                self.cat.position[0],
                new_y + self.cat.collider.size[1] / 2 + self.cat.hitbox_vertical_offset,
                self.cat.position[2]
            ]

            temp_collider = Box(new_collider_position, self.cat.collider.size)
            temp_collider.rotation = self.cat.rotation_y

            collision, collision_point = self.check_collision_with_top(temp_collider, self.box)
            if collision and self.cat.jump_mechanics.jump_velocity < 0:
                self.cat.position[1] = collision_point[1] - self.cat.collider.size[1] / 2 - self.cat.hitbox_vertical_offset
                self.cat.jump_mechanics.land()
            else:
                self.cat.position[1] = new_y

            self.cat.collider.position = [
                self.cat.position[0],
                self.cat.position[1] + self.cat.collider.size[1] / 2 + self.cat.hitbox_vertical_offset,
                self.cat.position[2]
            ]

            if self.cat.position[1] <= self.cat.initial_y:
                self.cat.position[1] = self.cat.initial_y
                self.cat.collider.position = [
                    self.cat.position[0],
                    self.cat.position[1] + self.cat.collider.size[1] / 2 + self.cat.hitbox_vertical_offset,
                    self.cat.position[2]
                ]
                self.cat.jump_mechanics.land()

        if not self.cat.jump_mechanics.is_jumping and not self.cat.is_flipping:
            if keys[pygame.K_f]:
                self.cat.start_flip(-1)  # Back flip
            elif keys[pygame.K_b]:
                self.cat.start_flip(1)   # Front flip

        if self.cat.is_flipping:
            new_y = self.cat.update_flip(dt)
            self.cat.position[1] = new_y
            self.cat.update_collider()

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
