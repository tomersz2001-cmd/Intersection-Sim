# spawner.py
import random
import math
from car import Car


class TrafficSpawner:
    def __init__(self, starting_edge, color, min_spawn_time=3.0, max_spawn_time=6.0):
        self.starting_edge = starting_edge  # NEW: Uses an Edge
        self.color = color
        self.min_spawn_time = min_spawn_time
        self.max_spawn_time = max_spawn_time
        self.timer = 0.0
        self.next_spawn_time = random.uniform(self.min_spawn_time, self.max_spawn_time)
        self.total_spawned = 0

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.next_spawn_time:
            can_spawn = True
            start_x, start_y = self.starting_edge.waypoints[0]

            if len(self.starting_edge.cars) > 0:
                last_car = self.starting_edge.cars[-1]
                distance = math.hypot(last_car.x - start_x, last_car.y - start_y)
                if distance < 60.0:
                    can_spawn = False

            if can_spawn:
                # NEW: Feed the starting edge to the car
                new_car = Car(starting_edge=self.starting_edge, color=self.color)
                self.starting_edge.add_car(new_car)

                self.total_spawned += 1
                self.timer = 0.0
                self.next_spawn_time = random.uniform(self.min_spawn_time, self.max_spawn_time)