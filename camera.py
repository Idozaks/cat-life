import math
from OpenGL.GL import *
from OpenGL.GLU import *

class Camera:
    def __init__(self, initial_position, initial_target, distance, sensitivity):
        self.position = list(initial_position)
        self.target = list(initial_target)
        self.distance = distance
        self.min_distance = 2.0  # Minimum camera distance
        self.max_distance = 20.0  # Increased maximum camera distance
        self.sensitivity = sensitivity
        self.zoom_sensitivity = 0.1  # Sensitivity for zoom (scrollwheel)
        self.angle_horizontal = 0
        self.angle_vertical = 30  # Decrease this for a less top-down view
        self.min_vertical_angle = -20  # Allow looking slightly upwards
        self.max_vertical_angle = 60   # Reduce maximum downward angle
        self.height_offset = 1.0  # Decrease height offset for a lower view

    def update(self, target_position, cat_collider):
        self.target = list(target_position)
        horizontal_rad = math.radians(self.angle_horizontal)
        vertical_rad = math.radians(self.angle_vertical)
        
        # Calculate new camera position
        new_x = self.target[0] + self.distance * math.cos(vertical_rad) * math.sin(horizontal_rad)
        new_y = self.target[1] + self.distance * math.sin(vertical_rad) + self.height_offset
        new_z = self.target[2] + self.distance * math.cos(vertical_rad) * math.cos(horizontal_rad)

        # Calculate the minimum allowed y position (bottom of cat's collider)
        min_y = cat_collider.position[1] - cat_collider.size[1] / 2 + self.height_offset

        # Adjust the camera position if it's below the minimum allowed y
        if new_y < min_y:
            # Calculate the angle needed to place the camera at the minimum y
            required_angle = math.asin((min_y - self.target[1] - self.height_offset) / self.distance)
            self.angle_vertical = math.degrees(required_angle)
            
            # Recalculate the camera position
            vertical_rad = math.radians(self.angle_vertical)
            new_y = self.target[1] + self.distance * math.sin(vertical_rad) + self.height_offset
            new_x = self.target[0] + self.distance * math.cos(vertical_rad) * math.sin(horizontal_rad)
            new_z = self.target[2] + self.distance * math.cos(vertical_rad) * math.cos(horizontal_rad)

        self.position = [new_x, new_y, new_z]

        glLoadIdentity()
        gluLookAt(
            self.position[0], self.position[1], self.position[2],
            self.target[0], self.target[1] + self.height_offset, self.target[2],
            0, 1, 0
        )

    def handle_mouse_motion(self, dx, dy):
        self.angle_horizontal -= dx * self.sensitivity
        self.angle_vertical -= dy * self.sensitivity
        
        # Clamp the vertical angle to prevent flipping and looking below the cat
        self.angle_vertical = max(self.min_vertical_angle, min(self.max_vertical_angle, self.angle_vertical))

    def handle_mouse_scroll(self, y):
        self.distance -= y * self.zoom_sensitivity
        self.distance = max(self.min_distance, min(self.max_distance, self.distance))

    def get_rotation(self):
        return self.angle_horizontal