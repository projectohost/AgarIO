from math import hypot
from pygame import *
import socketio
from random import randint

#  доставити силку на хостинг =>
SERVER_URL = "URLka"

sio = socketio.Client(reconnection=True, reconnection_attempts=10, reconnection_delay=1)

my_player = {"x": 0, "y": 0, "r": 20, "color": (255, 255, 255), "name": ""}
all_players = {}
sid = None
lose = False

def generate_food():
    return [
        {"x": randint(-3000, 3000), "y": randint(-3000, 3000), "r": 10,
         "c": (randint(50, 255), randint(50, 255), randint(50, 255))}
        for _ in range(300)
    ]

foods = generate_food()

init()
WIDTH, HEIGHT = 900, 700
screen = display.set_mode((WIDTH, HEIGHT))
clock = time.Clock()

def respawn():
    global lose, my_player, foods, zoom, sio

    print("Respawning...")

    lose = False
    my_player = {"x": 0, "y": 0, "r": 20, "color": (255, 255, 255), "name": ""}
    foods = generate_food()
    zoom = 1.0

    try:
        sio.disconnect()
    except:
        pass
    sio.connect(SERVER_URL, transports=["websocket"])

@sio.on("connect")
def on_connect():
    global sid
    sid = sio.sid
    print("Connected:", sid)


@sio.on("you_died")
def on_you_died(_=None):
    global lose
    lose = True
    print("Ви програли!")


@sio.on("state_update")
def on_state_update(data):
    global all_players
    all_players = data["players"]
    print(data)

def eat_food_local():
    if lose:
        return

    global foods, my_player
    eaten = []

    px, py, pr = my_player["x"], my_player["y"], my_player["r"]

    for f in foods:
        if hypot(f["x"] - px, f["y"] - py) <= pr + f["r"]:
            eaten.append(f)
            my_player["r"] += int(f["r"] * 0.5)

    for f in eaten:
        foods.remove(f)
        foods.append({
            "x": randint(-3000, 3000),
            "y": randint(-3000, 3000),
            "r": 10,
            "c": (randint(50, 255), randint(50, 255), randint(50, 255))
        })

    if eaten:
        sio.emit("set_radius", {"r": my_player["r"]})

zoom = 1.0
zoom_speed = 0.05

sio.connect(SERVER_URL, transports=["websocket"])

running = True

while running:
    for e in event.get():
        if e.type == QUIT:
            running = False

    screen.fill((25, 25, 25))

    keys = key.get_pressed()

    # ---------- респавн та реконект ----------
    if lose and keys[K_r]:
        respawn()
        continue

    if not lose:
        speed = 6
        if keys[K_w]: my_player["y"] -= speed
        if keys[K_s]: my_player["y"] += speed
        if keys[K_a]: my_player["x"] -= speed
        if keys[K_d]: my_player["x"] += speed
        if sio.connected:
            sio.emit("update_player", {"x": my_player["x"], "y": my_player["y"]})
        eat_food_local()

    if not lose and sid in all_players:
        p = all_players[sid]
        my_player["color"] = tuple(p["color"])
        my_player["name"] = p["name"]
        my_player["r"] = p["r"]

    # --------- зближення камери ---------
    target_zoom = 20 / max(my_player["r"], 20)
    zoom += (target_zoom - zoom) * zoom_speed

    cx, cy = my_player["x"], my_player["y"]

    # -------- Промальовка їжі --------
    for f in foods:
        fx = (f["x"] - cx) * zoom + WIDTH // 2
        fy = (f["y"] - cy) * zoom + HEIGHT // 2
        draw.circle(screen, f["c"],
            (int(fx), int(fy)),
            max(1, int(f["r"] * zoom)))

    # -------- Показ гравців  --------
    for pid, p in all_players.items():
        px = (p["x"] - cx) * zoom + WIDTH // 2
        py = (p["y"] - cy) * zoom + HEIGHT // 2
        draw.circle(screen, p["color"], (int(px), int(py)), int(p["r"] * zoom))

        fnt = font.SysFont("arial", max(12, int(16 * zoom)))
        nm = fnt.render(p["name"], True, (255, 255, 255))
        screen.blit(nm, (px - nm.get_width()//2, py - p["r"] * zoom - 20))

    # -------- лузер ;) --------
    if lose:
        fnt = font.SysFont("arial", 60)
        surf = fnt.render("Ви програли!", True, (255, 50, 50))
        screen.blit(surf, (
            WIDTH//2 - surf.get_width()//2,
            HEIGHT//2 - surf.get_height()//2
        ))

    display.flip()
    clock.tick(25)

quit()
