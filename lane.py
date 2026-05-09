# lane.py
import pygame


class Lane:
    def __init__(self, orientation, fixed_coord):
        self.orientation = orientation
        self.fixed_coord = fixed_coord
        self.cars = []

    def add_car(self, car):
        self.cars.append(car)

    def update_and_draw(self, dt, screen, light_pos, light_color):
        for i in range(len(self.cars)):
            car = self.cars[i]
            closest_obs_pos = 10000.0
            closest_obs_v = car.v0

            if i > 0:
                car_ahead = self.cars[i - 1]
                closest_obs_pos = car_ahead.pos
                closest_obs_v = car_ahead.v

            light_active = False

            if light_color == 'green':
                car.decision = None
            elif light_color == 'yellow':
                dist_to_light = light_pos - (car.pos + car.length)
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

            if light_active:
                dist_to_line = light_pos - (car.pos + car.length)
                # CHANGED: Slide threshold lowered to 10.0 for smaller scale
                if dist_to_line > 0 or (dist_to_line > -10.0 and car.v < 15.0):
                    if light_pos < closest_obs_pos:
                        closest_obs_pos = light_pos
                        closest_obs_v = 0.0

            is_alert = False
            # CHANGED: Line of sight scaled down to 100 pixels
            if light_color == 'green' and (light_pos - car.pos) < 100.0:
                is_alert = True

            car.update_physics(dt, closest_obs_pos, closest_obs_v, is_alert)

            # --- CHANGED: Car width reduced to 10 ---
            if self.orientation == 'horizontal':
                rect = (car.pos, self.fixed_coord, car.length, 10)
            else:
                rect = (self.fixed_coord, car.pos, 10, car.length)
            pygame.draw.rect(screen, car.color, rect)

        finished_cars = []
        surviving_cars = []
        for car in self.cars:
            # CHANGED: Extended from 1000 to 1500 to account for wider screen
            if car.pos > 1500.0:
                finished_cars.append(car)
            else:
                surviving_cars.append(car)
        self.cars = surviving_cars

        return finished_cars