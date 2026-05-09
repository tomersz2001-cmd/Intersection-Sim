# car.py
import random


class Car:
    def __init__(self, start_pos, color):
        # --- SCALED DOWN PHYSICAL PROPERTIES ---
        self.pos = start_pos
        self.v = 0.0
        self.a = 0.0
        self.length = 20.0  # CHANGED: Was 40.0
        self.color = color

        # --- SCALED DOWN IDM PARAMETERS ---
        self.v0 = random.uniform(65.0, 80.0)  # CHANGED: Was 130-160
        self.a_max = random.uniform(15.0, 25.0)  # CHANGED: Was 30-50
        self.b_max = random.uniform(20.0, 35.0)  # CHANGED: Was 40-70
        self.s0 = 10.0  # CHANGED: Safe gap halved to 10.0

        self.T = random.uniform(1.2, 1.8)
        self.delta = 4.0
        self.reaction_time = random.uniform(0.3, 0.7)

        self.time_alive = 0.0
        self.time_waiting = 0.0
        self.distance_traveled = 0.0

        self.memory = []
        self.crashed = False
        self.decision = None

    def update_physics(self, dt, actual_obstacle_pos, actual_obstacle_v, is_alert=False):
        if dt <= 0 or self.crashed: return

        self.time_alive += dt

        if self.pos > 0:
            self.distance_traveled += self.v * dt
            # CHANGED: Crawling speed threshold lowered to match the new scale
            if self.v < 5.0:
                self.time_waiting += dt

        actual_distance = actual_obstacle_pos - (self.pos + self.length)
        if actual_distance <= 0:
            self.pos = actual_obstacle_pos - self.length
            self.v = 0.0
            self.a = 0.0
            self.crashed = True
            self.color = (255, 0, 0)
            return

        actual_delta_v = self.v - actual_obstacle_v
        self.memory.append((actual_distance, actual_delta_v))

        frames = 1 if is_alert else max(1, int(self.reaction_time / dt))
        while len(self.memory) > frames: self.memory.pop(0)
        p_dist, p_dv = self.memory[0]

        s_star = self.s0 + (self.v * self.T) + (self.v * p_dv) / (2.0 * (self.a_max * self.b_max) ** 0.5)
        if s_star < self.s0: s_star = self.s0
        self.a = self.a_max * (1.0 - (self.v / self.v0) ** self.delta - (s_star / p_dist) ** 2)

        self.a = max(self.a, -250.0)
        self.v += self.a * dt
        if self.v < 0: self.v = 0.0
        self.pos += self.v * dt