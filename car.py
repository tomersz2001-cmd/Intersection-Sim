# car.py
import random
import math

# --- THE REALITY SCALE ---
# 1 Meter = 4 Pixels.
# A standard sedan is ~5m long, which equals 20 pixels on our screen.
METER = 4.0


class Car:
    def __init__(self, starting_edge, color):
        self.current_edge = starting_edge
        self.waypoints = self.current_edge.waypoints

        self.x, self.y = self.waypoints[0]
        self.target_wp_idx = 1
        self.heading = 0.0
        self.finished_path = False

        self.v = 0.0
        self.a = 0.0
        self.length = 5.0 * METER  # 5 meters long (20 pixels)
        self.width = 2.0 * METER  # 2 meters wide (8 pixels)
        self.color = color

        # --- HUMAN IMPERFECTIONS (SCALED TO REALITY) ---
        # City Speed Limit: ~40 to 60 km/h (which is 11 to 16.6 meters/second)
        speed_ms = random.uniform(11.0, 16.6)
        self.v0 = speed_ms * METER

        # Comfortable Acceleration: ~1.5 to 2.5 m/s^2
        accel_ms2 = random.uniform(1.5, 2.5)
        self.a_max = accel_ms2 * METER

        # Comfortable to Hard Braking: ~3.0 to 5.0 m/s^2
        brake_ms2 = random.uniform(3.0, 5.0)
        self.b_max = brake_ms2 * METER

        # Gap distance: 2 to 4 meters bumper-to-bumper
        self.s0 = random.uniform(2.0, 4.0) * METER

        self.T = random.uniform(1.2, 1.8)
        self.delta = 4.0

        self.reaction_time = random.uniform(0.4, 0.9)
        self.alert_reaction_time = random.uniform(0.05, 0.25)

        self.time_alive = 0.0
        self.time_waiting = 0.0
        self.distance_traveled = 0.0
        self.memory = [(1000.0, 0.0)]
        self.crashed = False

    def update_physics(self, dt, actual_distance, actual_obstacle_v, is_alert=False):
        if dt <= 0 or self.crashed or self.finished_path: return

        self.time_alive += dt
        if self.target_wp_idx > 0:
            self.distance_traveled += self.v * dt
            if self.v < (1.0 * METER): self.time_waiting += dt

        if actual_distance <= 0:
            self.v, self.a, self.crashed, self.color = 0.0, 0.0, True, (255, 0, 0)
            return

        actual_delta_v = self.v - actual_obstacle_v
        self.memory.append((actual_distance, actual_delta_v))

        delay = self.alert_reaction_time if is_alert else self.reaction_time
        frames = max(1, int(delay / dt))

        while len(self.memory) > frames: self.memory.pop(0)
        p_dist, p_dv = self.memory[0]

        s_star = self.s0 + (self.v * self.T) + (self.v * p_dv) / (2.0 * (self.a_max * self.b_max) ** 0.5)
        if s_star < self.s0: s_star = self.s0

        self.a = self.a_max * (1.0 - (self.v / self.v0) ** self.delta - (s_star / p_dist) ** 2)
        # Max emergency braking is around 9 m/s^2 (36 pixels/s^2)
        self.a = max(self.a, -9.0 * METER)
        self.v += self.a * dt
        if self.v < 0: self.v = 0.0

    def update_kinematics(self, dt):
        if self.crashed or self.finished_path: return

        target_x, target_y = self.waypoints[self.target_wp_idx]
        dx = target_x - self.x
        dy = target_y - self.y
        distance_to_wp = math.hypot(dx, dy)

        if distance_to_wp < 5.0:
            self.target_wp_idx += 1
            if self.target_wp_idx >= len(self.waypoints):
                out_edges = self.current_edge.end_node.out_edges
                if len(out_edges) == 0:
                    self.finished_path = True
                    return
                else:
                    next_edge = random.choice(out_edges)
                    self.current_edge.cars.remove(self)
                    self.current_edge = next_edge
                    self.current_edge.cars.append(self)
                    self.waypoints = self.current_edge.waypoints
                    self.target_wp_idx = 1
                    target_x, target_y = self.waypoints[self.target_wp_idx]
                    dx, dy = target_x - self.x, target_y - self.y

        self.heading = math.atan2(dy, dx)
        self.x += math.cos(self.heading) * self.v * dt
        self.y += math.sin(self.heading) * self.v * dt