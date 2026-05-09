# main.py
import pygame
import sys
import car
import lane
import spawner

print("=== TRAFFIC SIMULATION ===")
print("1. Pre-timed Algorithm (Fixed 6s Green)")
print("2. Smart Adaptive Algorithm (Sensor-based)")
algo_choice = input("Enter 1 or 2: ")

if algo_choice not in ['1', '2']:
    print("Invalid choice, defaulting to 1.")
    algo_choice = '1'

# ==========================================
# SETUP & WIDESCREEN GEOMETRY
# ==========================================
pygame.init()

WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(f"Widescreen Traffic Sim - Mode: {'Smart' if algo_choice == '2' else 'Pre-Timed'}")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20)

CX, CY = WIDTH // 2, HEIGHT // 2

lane_h = lane.Lane(orientation='horizontal', fixed_coord=CY - 5)
lane_v = lane.Lane(orientation='vertical', fixed_coord=CX - 5)

h_light_pos = CX - 20
v_light_pos = CY - 20

spawner_h = spawner.TrafficSpawner(lane_h, start_pos=-100.0, color=(0, 200, 255), min_spawn_time=0.5,
                                   max_spawn_time=7.0)
spawner_v = spawner.TrafficSpawner(lane_v, start_pos=-100.0, color=(0, 255, 100), min_spawn_time=1.0,
                                   max_spawn_time=10.0)

light_timer = 0.0
state = 'H_GREEN'
global_timer = 0.0

total_cars_passed = 0
total_delay_time = 0.0
total_distance = 0.0
total_time_alive = 0.0

PX_TO_KMH = 0.81

running = True

# ==========================================
# SIMULATION LOOP
# ==========================================
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    dt = clock.tick(60) / 1000.0
    global_timer += dt

    spawner_h.update(dt)
    spawner_v.update(dt)

    h_approaching = sum(1 for c in lane_h.cars if 0 < (h_light_pos - c.pos) < 250 and c.v > 5)
    v_approaching = sum(1 for c in lane_v.cars if 0 < (v_light_pos - c.pos) < 250 and c.v > 5)

    h_waiting = sum(1 for c in lane_h.cars if 0 < (h_light_pos - c.pos) < 350 and c.v < 5)
    v_waiting = sum(1 for c in lane_v.cars if 0 < (v_light_pos - c.pos) < 350 and c.v < 5)

    light_timer += dt

    if algo_choice == '1':
        if state == 'H_GREEN' and light_timer > 6.0:
            state = 'H_YELLOW'
            light_timer = 0.0
        elif state == 'V_GREEN' and light_timer > 6.0:
            state = 'V_YELLOW'
            light_timer = 0.0

    elif algo_choice == '2':
        if state == 'H_GREEN':
            if light_timer > 15.0 or (light_timer > 4.0 and h_approaching == 0 and v_waiting > 0):
                state = 'H_YELLOW'
                light_timer = 0.0
        elif state == 'V_GREEN':
            if light_timer > 15.0 or (light_timer > 4.0 and v_approaching == 0 and h_waiting > 0):
                state = 'V_YELLOW'
                light_timer = 0.0

    if state == 'H_YELLOW' and light_timer > 3.0:
        state = 'ALL_RED_1'
        light_timer = 0.0
    elif state == 'ALL_RED_1' and light_timer > 1.0:
        state = 'V_GREEN'
        light_timer = 0.0
    elif state == 'V_YELLOW' and light_timer > 3.0:
        state = 'ALL_RED_2'
        light_timer = 0.0
    elif state == 'ALL_RED_2' and light_timer > 1.0:
        state = 'H_GREEN'
        light_timer = 0.0

    if state == 'H_GREEN':
        h_color, v_color, h_rgb, v_rgb = 'green', 'red', (0, 255, 0), (255, 0, 0)
    elif state == 'H_YELLOW':
        h_color, v_color, h_rgb, v_rgb = 'yellow', 'red', (255, 255, 0), (255, 0, 0)
    elif state == 'ALL_RED_1' or state == 'ALL_RED_2':
        h_color, v_color, h_rgb, v_rgb = 'red', 'red', (255, 0, 0), (255, 0, 0)
    elif state == 'V_GREEN':
        h_color, v_color, h_rgb, v_rgb = 'red', 'green', (255, 0, 0), (0, 255, 0)
    elif state == 'V_YELLOW':
        h_color, v_color, h_rgb, v_rgb = 'red', 'yellow', (255, 0, 0), (255, 255, 0)

    # --- DRAW PHYSICAL WORLD ---
    screen.fill((50, 50, 50))
    pygame.draw.rect(screen, (80, 80, 80), (0, CY - 20, WIDTH, 40))
    pygame.draw.rect(screen, (80, 80, 80), (CX - 20, 0, 40, HEIGHT))

    pygame.draw.line(screen, h_rgb, (h_light_pos, CY - 20), (h_light_pos, CY + 20), 4)
    pygame.draw.line(screen, v_rgb, (CX - 20, v_light_pos), (CX + 20, v_light_pos), 4)

    deleted_h = lane_h.update_and_draw(dt, screen, h_light_pos, h_color)
    deleted_v = lane_v.update_and_draw(dt, screen, v_light_pos, v_color)

    for finished_car in (deleted_h + deleted_v):
        total_cars_passed += 1
        total_delay_time += finished_car.time_waiting
        total_distance += finished_car.distance_traveled
        total_time_alive += finished_car.time_alive

        # --- DASHBOARD CALCULATIONS ---
    sim_minutes = int(global_timer // 60)
    sim_seconds = int(global_timer % 60)
    timer_string = f"{sim_minutes:02d}:{sim_seconds:02d}"

    total_spawns = spawner_h.total_spawned + spawner_v.total_spawned
    avg_spawn_rate = (global_timer / total_spawns) if total_spawns > 0 else 0.0

    # --- NEW: Master Memory Tracker ---
    total_cars_in_memory = len(lane_h.cars) + len(lane_v.cars)

    live_cars = [c for c in (lane_h.cars + lane_v.cars) if c.pos > 0]
    active_count = len(live_cars)
    waiting_count = sum(1 for c in live_cars if c.v < 5.0)

    live_avg_speed_px = sum(c.v for c in live_cars) / active_count if active_count > 0 else 0.0
    live_speed_kmh = live_avg_speed_px * PX_TO_KMH

    hist_avg_delay = (total_delay_time / total_cars_passed) if total_cars_passed > 0 else 0.0
    hist_avg_speed_px = (total_distance / total_time_alive) if total_time_alive > 0 else 0.0
    hist_speed_kmh = hist_avg_speed_px * PX_TO_KMH

    minutes_elapsed = global_timer / 60.0
    cars_per_min = (total_cars_passed / minutes_elapsed) if minutes_elapsed > 0 else 0.0

    # --- DRAW DASHBOARD UI ---
    # Top Box (Live Data) - Increased height to 170
    pygame.draw.rect(screen, (30, 30, 30), (10, 10, 260, 170))
    pygame.draw.rect(screen, (0, 255, 255), (10, 10, 260, 170), 2)

    # Bottom Box (Historical Data) - Pushed down to Y=190
    pygame.draw.rect(screen, (30, 30, 30), (10, 190, 260, 160))
    pygame.draw.rect(screen, (255, 255, 255), (10, 190, 260, 160), 2)

    # Render Live Data Text
    screen.blit(font.render(f"--- LIVE ({'Smart' if algo_choice == '2' else 'Timed'}) ---", True, (0, 255, 255)),
                (20, 15))
    screen.blit(font.render(f"Sim Time: {timer_string}", True, (255, 255, 255)), (20, 45))
    screen.blit(font.render(f"Avg Spawn Rate: 1 every {avg_spawn_rate:.1f}s", True, (200, 200, 200)), (20, 75))
    screen.blit(font.render(f"Inst. Speed: {live_speed_kmh:.1f} km/h", True, (255, 255, 255)), (20, 105))
    screen.blit(font.render(f"Cars in Memory: {total_cars_in_memory}", True, (150, 150, 255)), (20, 135))  # NEW LINE

    # Render Historical Data Text
    screen.blit(font.render("--- OVERALL GRADES ---", True, (255, 255, 255)), (20, 195))
    screen.blit(font.render(f"Throughput: {cars_per_min:.1f} /min", True, (255, 255, 255)), (20, 225))
    screen.blit(font.render(f"Avg Trip Speed: {hist_speed_kmh:.1f} km/h", True, (200, 200, 200)), (20, 255))
    screen.blit(font.render(f"Overall Avg Delay: {hist_avg_delay:.1f} s", True, (255, 100, 100)), (20, 285))
    screen.blit(font.render(f"Currently Stopped: {waiting_count}", True, (255, 100, 100)), (20, 315))

    pygame.display.flip()

pygame.quit()
sys.exit()