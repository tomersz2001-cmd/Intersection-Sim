# main.py
import os

os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import sys
import math
import spawner
from graph import Node, Edge
import server
from car import METER


def get_signed_distance(car, target_x, target_y):
    dx, dy = target_x - car.x, target_y - car.y
    return (dx * math.cos(car.heading)) + (dy * math.sin(car.heading))


# --- NEW: MAP GENERATOR ---
def build_4_way_intersection(CX, CY, WIDTH, HEIGHT):
    """Generates the nodes and edges for a standard 4-way cross."""
    n_sp_w = Node("sp_w", -100, CY + 15);
    n_sp_e = Node("sp_e", WIDTH + 100, CY - 15)
    n_sp_n = Node("sp_n", CX - 15, -100);
    n_sp_s = Node("sp_s", CX + 15, HEIGHT + 100)
    n_ex_e = Node("ex_e", WIDTH + 100, CY + 15);
    n_ex_w = Node("ex_w", -100, CY - 15)
    n_ex_s = Node("ex_s", CX - 15, HEIGHT + 100);
    n_ex_n = Node("ex_n", CX + 15, -100)

    n_in_w = Node("in_w", CX - 40, CY + 15);
    n_in_e = Node("in_e", CX + 40, CY - 15)
    n_in_n = Node("in_n", CX - 15, CY - 40);
    n_in_s = Node("in_s", CX + 15, CY + 40)

    n_out_e = Node("out_e", CX + 40, CY + 15);
    n_out_w = Node("out_w", CX - 40, CY - 15)
    n_out_s = Node("out_s", CX - 15, CY + 40);
    n_out_n = Node("out_n", CX + 15, CY - 40)

    e_app_w = Edge("app_w", n_sp_w, n_in_w);
    e_app_e = Edge("app_e", n_sp_e, n_in_e)
    e_app_n = Edge("app_n", n_sp_n, n_in_n);
    e_app_s = Edge("app_s", n_sp_s, n_in_s)
    e_str_w = Edge("str_w", n_in_w, n_out_e);
    e_str_e = Edge("str_e", n_in_e, n_out_w)
    e_str_n = Edge("str_n", n_in_n, n_out_s);
    e_str_s = Edge("str_s", n_in_s, n_out_n)

    e_trn_w = Edge("trn_w", n_in_w, n_out_s, Node("c_nw", CX - 15, CY + 15))
    e_trn_e = Edge("trn_e", n_in_e, n_out_n, Node("c_se", CX + 15, CY - 15))
    e_trn_n = Edge("trn_n", n_in_n, n_out_w, Node("c_ne", CX - 15, CY - 15))
    e_trn_s = Edge("trn_s", n_in_s, n_out_e, Node("c_sw", CX + 15, CY + 15))

    e_dep_w = Edge("dep_w", n_out_w, n_ex_w);
    e_dep_e = Edge("dep_e", n_out_e, n_ex_e)
    e_dep_n = Edge("dep_n", n_out_n, n_ex_n);
    e_dep_s = Edge("dep_s", n_out_s, n_ex_s)

    edges = [e_app_w, e_app_e, e_app_n, e_app_s, e_str_w, e_str_e, e_str_n, e_str_s, e_trn_w, e_trn_e, e_trn_n, e_trn_s,
             e_dep_w, e_dep_e, e_dep_n, e_dep_s]

    spwns = [
        spawner.TrafficSpawner(e_app_w, color=(0, 200, 255), min_spawn_time=3.0, max_spawn_time=5.0),
        spawner.TrafficSpawner(e_app_e, color=(255, 150, 0), min_spawn_time=3.0, max_spawn_time=5.0),
        spawner.TrafficSpawner(e_app_n, color=(0, 255, 100), min_spawn_time=3.0, max_spawn_time=5.0),
        spawner.TrafficSpawner(e_app_s, color=(255, 100, 255), min_spawn_time=3.0, max_spawn_time=5.0)
    ]
    return edges, spwns, e_app_w, e_app_e, e_app_n, e_app_s


pygame.init()
WIDTH, HEIGHT = 1200, 800
clock = pygame.time.Clock()
CX, CY = WIDTH // 2, HEIGHT // 2

# Load Map
all_edges, spawners, e_app_w, e_app_e, e_app_n, e_app_s = build_4_way_intersection(CX, CY, WIDTH, HEIGHT)

light_timer = 0.0
state = 'H_GREEN'

server.run_in_background()
running = True
print("Headless Physics Engine Started. Scale is set to Real-World physics. Open index.html in your browser!")

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False

    dt = clock.tick(60) / 1000.0
    cmds = server.get_commands()

    # Update Spawners
    spawners[0].min_spawn_time, spawners[0].max_spawn_time = cmds["spawn_rate_h"] * 0.8, cmds["spawn_rate_h"] * 1.2
    spawners[1].min_spawn_time, spawners[1].max_spawn_time = cmds["spawn_rate_h"] * 0.8, cmds["spawn_rate_h"] * 1.2
    spawners[2].min_spawn_time, spawners[2].max_spawn_time = cmds["spawn_rate_v"] * 0.8, cmds["spawn_rate_v"] * 1.2
    spawners[3].min_spawn_time, spawners[3].max_spawn_time = cmds["spawn_rate_v"] * 0.8, cmds["spawn_rate_v"] * 1.2

    for s in spawners: s.update(dt)
    all_live_cars = [c for edge in all_edges for c in edge.cars]

    # --- THE ALGORITHM CONTROLLER ---
    light_timer += dt

    if cmds["algorithm"] == "timed":
        # DUMB TIMED MODE (Ignores traffic, blindly swaps every 12 seconds)
        if state == 'H_GREEN' and light_timer > 12.0:
            state, light_timer = 'H_YELLOW', 0.0
        elif state == 'V_GREEN' and light_timer > 12.0:
            state, light_timer = 'V_YELLOW', 0.0
        elif state == 'H_YELLOW' and light_timer > 3.0:
            state, light_timer = 'ALL_RED_1', 0.0
        elif state == 'ALL_RED_1' and light_timer > 1.0:
            state, light_timer = 'V_GREEN', 0.0
        elif state == 'V_YELLOW' and light_timer > 3.0:
            state, light_timer = 'ALL_RED_2', 0.0
        elif state == 'ALL_RED_2' and light_timer > 1.0:
            state, light_timer = 'H_GREEN', 0.0

    else:
        # SMART SENSOR MODE (Checks for waiting cars and empty lanes)
        h_wait = sum(1 for c in e_app_w.cars + e_app_e.cars if
                     c.v < (1.0 * METER) and get_signed_distance(c, c.current_edge.end_node.x,
                                                                 c.current_edge.end_node.y) > 0)
        v_wait = sum(1 for c in e_app_n.cars + e_app_s.cars if
                     c.v < (1.0 * METER) and get_signed_distance(c, c.current_edge.end_node.x,
                                                                 c.current_edge.end_node.y) > 0)
        h_app = sum(1 for c in e_app_w.cars + e_app_e.cars if
                    c.v > (1.0 * METER) and get_signed_distance(c, c.current_edge.end_node.x,
                                                                c.current_edge.end_node.y) > 0)
        v_app = sum(1 for c in e_app_n.cars + e_app_s.cars if
                    c.v > (1.0 * METER) and get_signed_distance(c, c.current_edge.end_node.x,
                                                                c.current_edge.end_node.y) > 0)

        if state == 'H_GREEN' and (light_timer > 15.0 or (light_timer > 4.0 and h_app == 0 and v_wait > 0)):
            state, light_timer = 'H_YELLOW', 0.0
        elif state == 'V_GREEN' and (light_timer > 15.0 or (light_timer > 4.0 and v_app == 0 and h_wait > 0)):
            state, light_timer = 'V_YELLOW', 0.0
        elif state == 'H_YELLOW' and light_timer > 3.0:
            state, light_timer = 'ALL_RED_1', 0.0
        elif state == 'ALL_RED_1' and light_timer > 1.0:
            state, light_timer = 'V_GREEN', 0.0
        elif state == 'V_YELLOW' and light_timer > 3.0:
            state, light_timer = 'ALL_RED_2', 0.0
        elif state == 'ALL_RED_2' and light_timer > 1.0:
            state, light_timer = 'H_GREEN', 0.0

    h_col = 'green' if state == 'H_GREEN' else 'yellow' if state == 'H_YELLOW' else 'red'
    v_col = 'green' if state == 'V_GREEN' else 'yellow' if state == 'V_YELLOW' else 'red'

    # --- PHYSICS & KINEMATICS ---
    for edge in all_edges:
        snapshot_cars = edge.cars[:]
        for i in range(len(snapshot_cars)):
            car = snapshot_cars[i]
            closest_obs_dist, closest_obs_v = 10000.0, car.v0

            if i > 0:
                car_ahead = snapshot_cars[i - 1]
                closest_obs_dist = math.hypot(car_ahead.x - car.x, car_ahead.y - car.y) - car.length
                closest_obs_v = car_ahead.v

            for other_car in all_live_cars:
                if other_car != car and not other_car.crashed:
                    if abs(other_car.x - car.x) > (15.0 * METER) or abs(other_car.y - car.y) > (15.0 * METER): continue
                    dist = math.hypot(other_car.x - car.x, other_car.y - car.y)
                    if dist < (10.0 * METER):
                        forward_dist = get_signed_distance(car, other_car.x, other_car.y)
                        dot_h = (math.cos(car.heading) * math.cos(other_car.heading)) + (
                                    math.sin(car.heading) * math.sin(other_car.heading))
                        if forward_dist > 0 and dot_h > 0.5:
                            real_dist = dist - car.length
                            if real_dist < closest_obs_dist:
                                closest_obs_dist, closest_obs_v = real_dist, other_car.v

            is_alert, my_light_col = False, None
            if edge in [e_app_w, e_app_e]:
                my_light_col = h_col
            elif edge in [e_app_n, e_app_s]:
                my_light_col = v_col

            if my_light_col:
                dist_to_light = get_signed_distance(car, edge.end_node.x, edge.end_node.y)
                front_bumper_to_light = dist_to_light - (car.length / 2)
                if 0 < front_bumper_to_light < closest_obs_dist:
                    if my_light_col != 'green':
                        safe_stop_distance = (car.v ** 2) / (2.0 * (car.b_max * 0.75)) + car.s0
                        if my_light_col == 'red' or (
                                my_light_col == 'yellow' and front_bumper_to_light > safe_stop_distance):
                            closest_obs_dist, closest_obs_v = front_bumper_to_light, 0.0
                if my_light_col == 'green' and car.v < (1.5 * METER) and 0 < dist_to_light < (
                        50.0 * METER): is_alert = True

            car.update_physics(dt, closest_obs_dist, closest_obs_v, is_alert)
            car.update_kinematics(dt)

        edge.cars = [c for c in edge.cars if not c.finished_path]

    server.update_data(all_live_cars, h_col, v_col)

pygame.quit()
sys.exit()