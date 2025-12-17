import os
import eventlet
import socketio
from random import randint, choice
from math import hypot
import string

# ----------------- Socket.IO server -----------------
sio = socketio.Server(cors_allowed_origins="*")
app = socketio.WSGIApp(sio)

# ----------------- Game state -----------------
players = {}

COLORS = [
    (255, 100, 100),
    (100, 255, 100),
    (100, 100, 255),
    (255, 255, 100),
    (255, 100, 255),
    (100, 255, 255)
]

def distance(p1, p2):
    return hypot(p1["x"] - p2["x"], p1["y"] - p2["y"])

# ----------------- Socket.IO events -----------------
@sio.event
def connect(sid, environ):
    print("Player connected:", sid)

    name = ''.join(choice(string.ascii_uppercase) for _ in range(4))

    players[sid] = {
        "x": randint(-500, 500),
        "y": randint(-500, 500),
        "r": 20,
        "color": choice(COLORS),
        "name": name
    }

    sio.emit("state_update", {"players": players})


@sio.event
def disconnect(sid):
    if sid in players:
        del players[sid]
    sio.emit("state_update", {"players": players})


@sio.on("update_player")
def update_player(sid, data):
    if sid not in players:
        return

    players[sid]["x"] = data["x"]
    players[sid]["y"] = data["y"]

    me = players[sid]

    # ---- collision check ----
    for pid, p in list(players.items()):
        if pid == sid:
            continue

        dist = distance(me, p)

        # me eats p
        if dist < me["r"] and me["r"] > p["r"] * 1.1:
            me["r"] += int(p["r"] * 0.7)
            del players[pid]
            print(sid, "ate", pid)
            sio.emit("state_update", {"players": players})
            sio.emit("you_died", {}, to=pid)   # notify loser
            return

        # p eats me
        elif dist < p["r"] and p["r"] > me["r"] * 1.1:
            p["r"] += int(me["r"] * 0.7)
            del players[sid]
            print(pid, "ate", sid)
            sio.emit("state_update", {"players": players})
            sio.emit("you_died", {}, to=sid)   # notify loser
            return

    sio.emit("state_update", {"players": players})


@sio.on("set_radius")
def set_radius(sid, data):
    if sid in players:
        players[sid]["r"] = data["r"]
        sio.emit("state_update", {"players": players})

# ----------------- Run server -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7500))
    print(f"Server starting on port {port}...")
    eventlet.wsgi.server(eventlet.listen(("0.0.0.0", port)), app)
