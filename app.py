import socketio
from random import randint, choice
from math import hypot
import string

# ASGI Socket.IO server (Render compatible)
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*"
)
app = socketio.ASGIApp(sio)

# Game state
players = {}
foods = [
    {
        "x": randint(-2000, 2000),
        "y": randint(-2000, 2000),
        "r": 10,
        "c": [randint(0, 255), randint(0, 255), randint(0, 255)]
    }
    for _ in range(300)
]


def random_name():
    return "".join(choice(string.ascii_uppercase + string.digits) for _ in range(3))


@sio.event
async def connect(sid, environ):
    players[sid] = {
        "x": randint(-500, 500),
        "y": randint(-500, 500),
        "r": 20,
        "color": [randint(0, 255), randint(0, 255), randint(0, 255)],
        "name": random_name()
    }

    print(f"Player {players[sid]['name']} connected.")

    await sio.emit("state_update", {
        "players": players,
        "foods": foods
    })


@sio.event
async def disconnect(sid):
    if sid in players:
        print(f"Player {players[sid]['name']} disconnected.")
        players.pop(sid, None)

    await sio.emit("state_update", {
        "players": players,
        "foods": foods
    })


@sio.event
async def update_player(sid, data):
    if sid not in players:
        return

    # Update player position
    p = players[sid]
    p["x"], p["y"] = data["x"], data["y"]

    # --- FOOD COLLISION ---
    eaten = []
    for f in foods:
        if hypot(f["x"] - p["x"], f["y"] - p["y"]) <= f["r"] + p["r"]:
            eaten.append(f)
            p["r"] += int(f["r"] * 0.3)

    for f in eaten:
        foods.remove(f)
        foods.append({
            "x": randint(-2000, 2000),
            "y": randint(-2000, 2000),
            "r": 10,
            "c": [randint(0, 255), randint(0, 255), randint(0, 255)]
        })

    # --- PLAYER COLLISION ---
    to_remove = []
    for sid2, other in list(players.items()):
        if sid2 == sid:
            continue

        dist = hypot(other["x"] - p["x"], other["y"] - p["y"])
        if dist <= other["r"] + p["r"]:

            # p eats other
            if p["r"] > other["r"] * 1.1:
                p["r"] += int(other["r"] * 0.4)
                to_remove.append(sid2)
                await sio.emit("player_lost", {"sid": sid2}, room=sid2)

            # other eats p
            elif other["r"] > p["r"] * 1.1:
                other["r"] += int(p["r"] * 0.4)
                to_remove.append(sid)
                await sio.emit("player_lost", {"sid": sid}, room=sid)
                break

    for sid_r in to_remove:
        players.pop(sid_r, None)

    # Send updated state to all players
    await sio.emit("state_update", {
        "players": players,
        "foods": foods
    })


# RUNNING:
# Render will run with: uvicorn server:app --host 0.0.0.0 --port $PORT
