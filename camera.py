import math
from OpenGL.GL import *
from OpenGL.GLU import *

class Camera:
    def __init__(self, initial_position, initial_target, distance, sensitivity):
        self.position = list(initial_position)
        self.target = list(initial_target)
        self.distance = distance
        self.sensitivity = sensitivity
        self.angle_horizontal = 0
        self.angle_vertical = 30
        self.min_vertical_angle = -89  # Prevent looking straight up
        self.max_vertical_angle = 89   # Prevent looking straight down
        self.height_offset = 0.5  # 0.5 meters above the cat's center

    def update(self, target_position, cat_collider):
        self.target = list(target_position)
        horizontal_rad = math.radians(self.angle_horizontal)
        vertical_rad = math.radians(self.angle_vertical)
        
        # Calculate new camera position
        new_x = self.target[0] + self.distance * math.cos(vertical_rad) * math.sin(horizontal_rad)
        new_y = self.target[1] + self.distance * math.sin(vertical_rad) + self.height_offset  # Add height_offset here
        new_z = self.target[2] + self.distance * math.cos(vertical_rad) * math.cos(horizontal_rad)

        # Calculate the minimum allowed y position (bottom of cat's collider)
        min_y = cat_collider.position[1] - cat_collider.size[1] / 2 + self.height_offset  # Add height_offset here as well

        # Adjust the camera position if it's below the minimum allowed y
        if new_y < min_y:
            # Calculate the angle needed to place the camera at the minimum y
            required_angle = math.asin((min_y - self.target[1] - self.height_offset) / self.distance)  # Adjust for height_offset
            self.angle_vertical = math.degrees(required_angle)
            
            # Recalculate the camera position
            vertical_rad = math.radians(self.angle_vertical)
            new_y = self.target[1] + self.distance * math.sin(vertical_rad) + self.height_offset  # Add height_offset
            new_x = self.target[0] + self.distance * math.cos(vertical_rad) * math.sin(horizontal_rad)
            new_z = self.target[2] + self.distance * math.cos(vertical_rad) * math.cos(horizontal_rad)

        self.position = [new_x, new_y, new_z]

        glLoadIdentity()
        gluLookAt(
            self.position[0], self.position[1], self.position[2],
            self.target[0], self.target[1] + self.height_offset, self.target[2],  # Adjust target y-position
            0, 1, 0
        )

    def handle_mouse_motion(self, dx, dy):
        self.angle_horizontal -= dx * self.sensitivity
        self.angle_vertical -= dy * self.sensitivity
        
        # Clamp the vertical angle to prevent flipping and looking below the cat
        self.angle_vertical = max(self.min_vertical_angle, min(self.max_vertical_angle, self.angle_vertical))

    def get_rotation(self):
        return self.angle_horizontal