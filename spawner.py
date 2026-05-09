# spawner.py
import random
from car import Car


class TrafficSpawner:
    """
    Generates cars automatically.
    Now accepts min and max spawn times so we can simulate heavy vs. light traffic!
    """

    def __init__(self, lane, start_pos, color, min_spawn_time=3.0, max_spawn_time=6.0):
        self.lane = lane
        self.start_pos = start_pos
        self.color = color

        # --- NEW: Configurable Traffic Density ---
        self.min_spawn_time = min_spawn_time
        self.max_spawn_time = max_spawn_time

        self.timer = 0.0
        # Roll the dice for the very first car using our custom times
        self.next_spawn_time = random.uniform(self.min_spawn_time, self.max_spawn_time)

        self.total_spawned = 0

    def update(self, dt):
        self.timer += dt

        if self.timer >= self.next_spawn_time:
            can_spawn = True

            # Safety Check: Don't spawn inside another car
            if len(self.lane.cars) > 0:
                last_car = self.lane.cars[-1]
                distance = abs(last_car.pos - self.start_pos)
                if distance < 60.0:
                    can_spawn = False

            if can_spawn:
                new_car = Car(start_pos=self.start_pos, color=self.color)
                self.lane.add_car(new_car)

                self.total_spawned += 1
                self.timer = 0.0

                # Roll the dice for the next car using our custom times
                self.next_spawn_time = random.uniform(self.min_spawn_time, self.max_spawn_time)