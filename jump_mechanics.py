import math
import time

class JumpMechanics:
    def __init__(self, initial_y, gravity, jump_height, max_jump_height, max_jump_hold_time):
        self.initial_y = initial_y
        self.gravity = gravity
        self.jump_height = jump_height
        self.max_jump_height = max_jump_height
        self.max_jump_hold_time = max_jump_hold_time
        
        self.is_jumping = False
        self.jump_start_time = 0
        self.jump_hold_time = 0
        self.jump_velocity = 0
        self.min_jump_velocity = math.sqrt(2 * abs(self.gravity) * (self.jump_height * 0.25))

    def start_jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.jump_start_time = time.time()
            self.jump_hold_time = 0
            self.jump_velocity = self.min_jump_velocity

    def update_jump(self, keys, dt, space_key):
        if self.is_jumping:
            current_time = time.time()
            if keys[space_key] and current_time - self.jump_start_time < self.max_jump_hold_time:
                self.jump_hold_time = current_time - self.jump_start_time
                jump_progress = min(self.jump_hold_time / self.max_jump_hold_time, 1)
                target_velocity = math.sqrt(2 * abs(self.gravity) * (self.jump_height + (self.max_jump_height - self.jump_height) * jump_progress))
                self.jump_velocity = min(self.jump_velocity + (target_velocity - self.jump_velocity) * dt * 10, target_velocity)
            else:
                self.jump_velocity += self.gravity * dt

        return self.jump_velocity * dt

    def land(self):
        self.is_jumping = False
        self.jump_velocity = 0
