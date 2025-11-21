from math import hypot
from pygame import *
import socketio

sio = socketio.Client()

my_player = {"x": 0, "y": 0, "r": 20, "color": (255, 255, 255), "name": ""}
all_players = {}
foods = []
lose = False
sid = None

init()
WIDTH, HEIGHT = 800, 600
screen = display.set_mode((WIDTH, HEIGHT))
clock = time.Clock()

sio.connect("http://localhost:5000")

@sio.on("connect")
def on_connect():
    global sid
    sid = sio.sid
    print("Connected with ID:", sid)

@sio.on("state_update")
def on_state_update(data):
    global all_players, foods
    all_players = data["players"]
    foods = data["foods"]
    print(all_players)


@sio.on("player_lost")
def on_player_lost(data):
    global lose, sid
    print(lose, data["sid"])
    if data["sid"] in all_players.keys():
        lose = True

running = True
current_zoom = 1.0  
zoom_speed = 0.05   
base_size = 20      

while running:
    for e in event.get():
        if e.type == QUIT:
            running = False

    screen.fill((30, 30, 30))

   
    keys = key.get_pressed()
    if not lose:
        speed = 5
        if keys[K_w]:
            my_player["y"] -= speed
        if keys[K_s]:
            my_player["y"] += speed
        if keys[K_a]:
            my_player["x"] -= speed
        if keys[K_d]:
            my_player["x"] += speed

        # Update server
        sio.emit("update_player", {"x": my_player["x"], 
                                   "y": my_player["y"]})

    if sid in all_players:
        my_player.update(all_players[sid])


    target_zoom = 20 / max(my_player["r"], 20)
    current_zoom += (target_zoom - current_zoom) * zoom_speed

    cx, cy = my_player["x"], my_player["y"]

    for f in foods:
        x = (f["x"] - cx) * current_zoom + WIDTH // 2
        y = (f["y"] - cy) * current_zoom + HEIGHT // 2
        draw.circle(screen, f["c"], 
                    (int(x), int(y)), 
                    int(f["r"] * current_zoom))

    for pid, p in all_players.items():
        x = (p["x"] - cx) * current_zoom + WIDTH // 2
        y = (p["y"] - cy) * current_zoom + HEIGHT // 2
        color = tuple(p["color"])
        draw.circle(screen, color, (int(x), 
                                    int(y)), 
                                    int(p["r"] * current_zoom))
        if "name" in p:
            fnt = font.SysFont("arial", int(14 * current_zoom) + 10)
            name_surf = fnt.render(p["name"], True, (255, 255, 255))
            screen.blit(name_surf, (x - name_surf.get_width() // 2, 
                                    y - p["r"] * current_zoom - 20))


    if lose:
        font.init()
        big_fnt = font.SysFont("arial", 64, True)
        text = big_fnt.render("YOU LOST!", True, (255, 50, 50))
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))

        small_fnt = font.SysFont("arial", 24)
        tip = small_fnt.render("Press R to respawn", True, (200, 200, 200))
        screen.blit(tip, (WIDTH // 2 - tip.get_width() // 2, HEIGHT // 2 + 50))

        if keys[K_r]:

            lose = False
            my_player["r"] = base_size
            sio.disconnect()
            sio.connect("http://localhost:5000")

    display.flip()
    clock.tick(60)

quit()
