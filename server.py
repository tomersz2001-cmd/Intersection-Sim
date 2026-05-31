# server.py
import asyncio
import websockets
import json
import threading

latest_traffic_data = '{"cars": [], "lights": {}}'
connected_clients = set()

ui_commands = {
    "spawn_rate_h": 4.0,
    "spawn_rate_v": 4.0,
    "algorithm": "smart"  # NEW: Tracks the current light behavior
}

def get_commands():
    return ui_commands

def update_data(cars, h_color, v_color):
    global latest_traffic_data
    car_data = [{"id": id(c), "x": round(c.x, 1), "y": round(c.y, 1), "heading": round(c.heading, 3), "color": f"rgb{c.color}", "l": c.length, "w": c.width} for c in cars]
    latest_traffic_data = json.dumps({"cars": car_data, "lights": {"horizontal": h_color, "vertical": v_color}})

async def broadcast_loop():
    while True:
        if connected_clients:
            websockets.broadcast(connected_clients, latest_traffic_data)
        await asyncio.sleep(1 / 30.0)

async def handler(websocket):
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            if data.get("type") == "update_spawn":
                if data["target"] == "H": ui_commands["spawn_rate_h"] = float(data["value"])
                elif data["target"] == "V": ui_commands["spawn_rate_v"] = float(data["value"])
            # NEW: Catch the algorithm change from the UI
            elif data.get("type") == "update_algo":
                ui_commands["algorithm"] = data["value"]
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.remove(websocket)

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print(">>> WEBSOCKET BRIDGE OPEN: Two-Way Comms Active <<<")
        await broadcast_loop()

def start_server():
    asyncio.run(main())

def run_in_background():
    t = threading.Thread(target=start_server, daemon=True)
    t.start()