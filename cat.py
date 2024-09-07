import math
from box import Box
from jump_mechanics import JumpMechanics
from objloader import OBJ

class Cat:
    def __init__(self, initial_position, gravity):
        self.cat = OBJ('models/cat.obj', swapyz=True)
        self.height = 0.5  # 0.25 * 2, doubled cat height in meters
        self.length = 1.8  # 0.9 * 2, doubled the previous length
        self.width = 0.4   # 0.20 * 2, doubled typical cat width in meters
        
        self.collider = Box([0, 0, 0], [self.width, self.height, self.length])
        self.hitbox_vertical_offset = 0.1  # 0.05 * 2, doubled 5 cm offset
        
        self.rotation_y = 45
        self.position = initial_position
        self.initial_y = self.position[1]
        self.base_speed = 2.0
        self.current_speed = self.base_speed
        self.max_speed = 6.0  # self.base_speed * 3
        self.acceleration_time = 1.0
        
        self.is_turning = False
        self.turn_progress = 0
        self.base_turn_speed = 2
        self.max_turn_speed = 6  # self.base_turn_speed * 3
        self.current_turn_speed = self.base_turn_speed

        self.is_flipping = False
        self.flip_progress = 0
        self.flip_height = 1.5
        self.flip_start_y = 0
        self.flip_rotation = 0
        self.flip_duration = 0.6
        self.flip_timer = 0
        self.flip_direction = 1

        self.jump_mechanics = JumpMechanics(
            initial_y=self.initial_y,
            gravity=gravity,
            jump_height=1.0,
            max_jump_height=1.5,
            max_jump_hold_time=0.3
        )

    def update_position(self, new_position):
        self.position = new_position
        self.collider.position = [
            self.position[0],
            self.position[1] + self.collider.size[1] / 2 + self.hitbox_vertical_offset,
            self.position[2]
        ]

    def start_flip(self, direction):
        self.is_flipping = True
        self.flip_timer = 0
        self.jump_mechanics.jump_velocity = math.sqrt(2 * abs(self.jump_mechanics.gravity) * self.flip_height)
        self.flip_start_y = self.position[1]
        self.flip_direction = direction
        self.flip_rotation = 0

    def update_flip(self, dt):
        self.flip_timer += dt
        self.jump_mechanics.jump_velocity += self.jump_mechanics.gravity * dt
        new_y = self.position[1] + self.jump_mechanics.jump_velocity * dt

        self.flip_rotation = (self.flip_timer / self.flip_duration) * 360 * self.flip_direction
        self.flip_rotation = max(0, min(abs(self.flip_rotation), 360)) * self.flip_direction

        if new_y <= self.initial_y:
            new_y = self.initial_y
            self.is_flipping = False
            self.flip_rotation = 0
            self.jump_mechanics.jump_velocity = 0

        return new_y

    def update_collider(self):
        self.collider.position = [
            self.position[0],
            self.position[1] + self.collider.size[1] / 2 + self.hitbox_vertical_offset,
            self.position[2]
        ]
        self.collider.rotation = self.rotation_y