# lane.py
import pygame
import math


class Lane:
    """
    Acts as a fleet manager for a group of cars sharing the same route.
    """

    def __init__(self, waypoints):
        # NEW: The lane simply holds the geometric route to hand to new cars
        self.waypoints = waypoints
        self.cars = []

    def add_car(self, car):
        self.cars.append(car)

    def update_and_draw(self, dt, screen, light_pos, light_color):
        # NEW: The light is now an X/Y coordinate
        light_x, light_y = light_pos

        for i in range(len(self.cars)):
            car = self.cars[i]

            # 1. Longitudinal Radar (Find the car directly ahead of us)
            closest_obs_dist = 10000.0
            closest_obs_v = car.v0

            if i > 0:
                car_ahead = self.cars[i - 1]
                # 2D Pythagorean theorem for distance
                dist = math.hypot(car_ahead.x - car.x, car_ahead.y - car.y)
                closest_obs_dist = dist - car.length  # Bumper to bumper
                closest_obs_v = car_ahead.v

            # 2. Traffic Light Dilemma Zone (Linear Algebra Magic)
            # Find the vector from the car to the traffic light
            dx = light_x - car.x
            dy = light_y - car.y

            # Find the car's forward directional vector
            forward_x = math.cos(car.heading)
            forward_y = math.sin(car.heading)

            # The Dot Product gives us the exact 1D distance to the line,
            # even if the car is driving diagonally!
            dist_to_light = (dx * forward_x + dy * forward_y) - (car.length / 2)

            light_active = False
            if light_color == 'green':
                car.decision = None

            elif light_color == 'yellow':
                if car.decision is None:
                    safe_stop_distance = (car.v ** 2) / (2.0 * (car.b_max * 0.75)) + car.s0
                    if dist_to_light > safe_stop_distance:
                        car.decision = 'stop'
                    else:
                        car.decision = 'go'
                if car.decision == 'stop':
                    light_active = True

            elif light_color == 'red':
                car.decision = 'stop'
                light_active = True

            # If stopping, treat the line as a physical obstacle
            if light_active:
                if dist_to_light > 0 or (dist_to_light > -10.0 and car.v < 15.0):
                    if dist_to_light < closest_obs_dist:
                        closest_obs_dist = dist_to_light
                        closest_obs_v = 0.0

            is_alert = False
            if light_color == 'green' and 0 < dist_to_light < 100.0:
                is_alert = True

            # 3. Update the Brain and the Steering Wheel
            car.update_physics(dt, closest_obs_dist, closest_obs_v, is_alert)
            car.update_kinematics(dt)

            # 4. Draw the Rotated 2D Car (The Rotation Matrix)
            l = car.length / 2
            w = car.width / 2

            # Base corners assuming the car is pointing straight right (0 degrees)
            corners = [
                (l, w),  # Front Right
                (l, -w),  # Front Left
                (-l, -w),  # Back Left
                (-l, w)  # Back Right
            ]

            rotated_corners = []
            for cx, cy in corners:
                # Rotate the corners mathematically around the car's center
                rx = car.x + (cx * math.cos(car.heading) - cy * math.sin(car.heading))
                ry = car.y + (cx * math.sin(car.heading) + cy * math.cos(car.heading))
                rotated_corners.append((rx, ry))

            pygame.draw.polygon(screen, car.color, rotated_corners)

        # 5. Garbage Collector (Now relies on the path completion flag)
        finished_cars = []
        surviving_cars = []
        for car in self.cars:
            if car.finished_path:
                finished_cars.append(car)
            else:
                surviving_cars.append(car)
        self.cars = surviving_cars

        return finished_cars