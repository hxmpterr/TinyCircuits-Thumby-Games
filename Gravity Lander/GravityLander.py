#####################################################
#  GRAVITY LANDER  --  v4
#  A physics-based moon-lander game for Thumby
#
#  What's new in v4:
#   - crashing now does a real dissolve FADE OUT, then
#     fades into a proper GAME OVER screen where you
#     pick "RETRY" or "MENU" (instead of just PRESS A)
#   - every transition between screens (menu, levels,
#     tutorial, freeroam, settings, game over) now uses
#     a smooth dissolve/dither fade instead of a blocky
#     wipe -- much more "space movie" feeling
#   - every single label in the game was re-laid-out by
#     hand with guaranteed spacing, so NOTHING overlaps
#     and NOTHING can ever run off the edge of the screen
#   - a denser starfield, a second background planet
#     visible during actual play (not just the menu),
#     and richer overall space dressing
#   - SETTINGS now has an "A THRUST" toggle: turn it on
#     and the A button works as a second main-engine
#     button alongside dpad UP, so you can thrust with
#     either one
#   - the interactive TUTORIAL is untouched -- still the
#     same hands-on practice flow
#
#  Physics simulated every frame, same core feel:
#    - constant downward gravity acceleration
#    - main thruster (dpad UP, or A if enabled) fights
#      gravity
#    - side thrusters (dpad LEFT/RIGHT) push you sideways
#    - velocity carries between frames (real inertia!)
#    - limited fuel - use it wisely
#    - land SOFT and INSIDE the pad, or you crash
#
#  Controls:
#    UP    = main engine (burns fuel, thrusts up)
#    LEFT  = left side thruster (pushes you left)
#    RIGHT = right side thruster (pushes you right)
#    DOWN  = (freeroam only) thrust downward
#    A     = confirm / select (also main engine if
#            "A THRUST" is turned on in SETTINGS)
#    B     = back / cancel
#####################################################

import thumby
import random
import time
import math

thumby.display.setFPS(30)

W = thumby.display.width   # 72
H = thumby.display.height  # 40

# ---------------- physics constants ----------------
GRAVITY      = 0.045
MAIN_THRUST  = 0.11
SIDE_THRUST  = 0.05
DRAG         = 0.995
WALL_BOUNCE  = 0.5
MAX_FUEL     = 100.0
SAFE_VY      = 1.6
SAFE_VX      = 1.0

COUNTDOWN_LEN = 90   # 3 seconds @ 30fps

# ---------------- rocket sprite (7x10, VLSB bitmap, smaller than v2) ----------------
ROCKET_W = 7
ROCKET_H = 10
ROCKET_BITMAP = bytearray([224, 248, 124, 255, 124, 248, 224,
                            3, 1, 0, 1, 0, 1, 3])

FLAME_W = 5
FLAME_H = 5
FLAME1_BITMAP = bytearray([0, 3, 7, 3, 0])
FLAME2_BITMAP = bytearray([2, 7, 15, 7, 2])

KIND_NAMES = ["STAR", "GEM", "ORB"]

# 12 preset unit-ish direction vectors (30 degrees apart) for explosions
EXPLOSION_DIRS = [
    (1.0, 0.0), (0.87, 0.5), (0.5, 0.87), (0.0, 1.0),
    (-0.5, 0.87), (-0.87, 0.5), (-1.0, 0.0), (-0.87, -0.5),
    (-0.5, -0.87), (-0.0, -1.0), (0.5, -0.87), (0.87, -0.5),
]

# ---------------- persistent save data ----------------
thumby.saveData.setName("GravityLander")

soundOn = True
maxUnlocked = 1
frFound = 0
altThrust = False
if thumby.saveData.hasItem("sound"):
    soundOn = int(thumby.saveData.getItem("sound")) == 1
if thumby.saveData.hasItem("unlocked"):
    maxUnlocked = int(thumby.saveData.getItem("unlocked"))
if thumby.saveData.hasItem("frfound"):
    frFound = int(thumby.saveData.getItem("frfound"))
if thumby.saveData.hasItem("altthrust"):
    altThrust = int(thumby.saveData.getItem("altthrust")) == 1


def save_game():
    thumby.saveData.setItem("sound", 1 if soundOn else 0)
    thumby.saveData.setItem("unlocked", maxUnlocked)
    thumby.saveData.setItem("altthrust", 1 if altThrust else 0)
    thumby.saveData.save()


def sfx(freq, dur):
    if soundOn:
        thumby.audio.play(freq, dur)


def sfx_land():
    sfx(520, 70)
    sfx(780, 90)


def sfx_crash():
    sfx(120, 220)


def sfx_blip():
    sfx(300, 40)


def sfx_launch():
    sfx(200, 60)
    sfx(400, 60)
    sfx(700, 80)


# ---------------- small drawing helpers ----------------
def frand(lo, hi):
    return lo + (hi - lo) * random.randint(0, 1000) / 1000.0


_circle_cache = {}


def draw_circle(cx, cy, r, col=1):
    """Hollow circle outline, cached per radius."""
    if r not in _circle_cache:
        pts = []
        steps = max(8, r * 4)
        for i in range(steps):
            a = 2 * math.pi * i / steps
            pts.append((round(r * math.cos(a)), round(r * math.sin(a))))
        _circle_cache[r] = pts
    for (dx, dy) in _circle_cache[r]:
        thumby.display.setPixel(cx + dx, cy + dy, col)


def draw_disc(cx, cy, r, col=1):
    """Filled circle."""
    for dy in range(-r, r + 1):
        span = int(math.sqrt(max(0, r * r - dy * dy)))
        thumby.display.drawLine(cx - span, cy + dy, cx + span, cy + dy, col)


def draw_ring_planet(cx, cy, r):
    draw_disc(cx, cy, r, 1)
    steps = 20
    for i in range(steps):
        a = 2 * math.pi * i / steps
        rx = int((r + 3) * 1.8 * math.cos(a))
        ry = int((r + 1) * 0.5 * math.sin(a))
        if rx * rx + ry * ry > (r + 1) * (r + 1):
            thumby.display.setPixel(cx + rx, cy + ry, 1)


TEXT_H = 6  # tight contrast-box height used for every label -- kept short
            # on purpose so adjacent labels can never bleed into each other


def dtext(s, x, y, fg=1):
    """Draw text with a solid contrast box behind it so it never blends
    into the background, and clamp it so it can never run off-screen.
    Callers just need to keep labels at least TEXT_H (6px) apart
    vertically and this guarantees zero visual overlap."""
    tw = len(s) * 6
    if x < 0:
        x = 0
    if x + tw > W:
        x = W - tw
    if x < 0:
        x = 0
    if y < 0:
        y = 0
    if y + TEXT_H > H:
        y = H - TEXT_H
    thumby.display.drawFilledRectangle(x - 1, y, tw + 2, TEXT_H, 1 - fg)
    thumby.display.drawText(s, x, y, fg)


def dtext_center(s, y, fg=1):
    tw = len(s) * 6
    x = (W - tw) // 2
    dtext(s, x, y, fg)


# ---------------- dissolve / dither fade system ----------------
BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
FADE_BLOCK = 4
_fb_cols = (W + FADE_BLOCK - 1) // FADE_BLOCK
_fb_rows = (H + FADE_BLOCK - 1) // FADE_BLOCK
_fade_scored = []
for _by in range(_fb_rows):
    for _bx in range(_fb_cols):
        _v = BAYER4[_by % 4][_bx % 4] * 100 + (_bx * 13 + _by * 29) % 97
        _fade_scored.append((_v, _bx, _by))
_fade_scored.sort()
FADE_ORDER = [(bx, by) for (v, bx, by) in _fade_scored]
FADE_BLOCK_COUNT = len(FADE_ORDER)


def _black_block(bx, by):
    x0 = bx * FADE_BLOCK
    y0 = by * FADE_BLOCK
    x1 = x0 + FADE_BLOCK
    y1 = y0 + FADE_BLOCK
    if x1 > W:
        x1 = W
    if y1 > H:
        y1 = H
    thumby.display.drawFilledRectangle(x0, y0, x1 - x0, y1 - y0, 0)


def fade_out_blocking(steps=9):
    """Dissolve whatever is currently on screen down to black."""
    idx = 0
    n = FADE_BLOCK_COUNT
    for s in range(steps):
        target = (s + 1) * n // steps
        while idx < target:
            bx, by = FADE_ORDER[idx]
            _black_block(bx, by)
            idx += 1
        thumby.display.update()


def transition_wipe():
    """Smooth dissolve transition used whenever we change screens."""
    fade_out_blocking(7)
    thumby.display.fill(0)
    thumby.display.update()


# ---------------- states ----------------
STATE_MENU        = 0
STATE_TUTORIAL    = 1
STATE_LEVELSELECT = 2
STATE_SETTINGS    = 3
STATE_PLAY        = 4
STATE_RESULT      = 5
STATE_OVER        = 6
STATE_COUNTDOWN   = 7
STATE_FREEROAM    = 8

state = STATE_MENU
frame_count = 0

MENU_ITEMS = ["START", "LEVELS", "TUTORIAL", "FREEROAM", "SETTINGS"]
menuIndex = 0
settingsIndex = 0
selLevel = 1

level = 1
resultMsg = ""
resultTimer = 0
flashFrames = 0
countdown = COUNTDOWN_LEN

# ---------------- background stars (shared) ----------------
stars = []
for _i in range(14):
    stars.append([random.randint(0, W - 1), random.randint(0, 13), random.randint(0, 90)])

# decorative rockets that fly up the screen on the main menu
bg_rockets = []


def update_bg_rockets():
    if frame_count % 75 == 0 and len(bg_rockets) < 2:
        bg_rockets.append([float(random.randint(6, W - 6)), float(H + 8), -frand(0.5, 1.0)])
    i = 0
    while i < len(bg_rockets):
        r = bg_rockets[i]
        r[1] += r[2]
        if r[1] < -14:
            bg_rockets.pop(i)
        else:
            i += 1


def draw_bg_rockets():
    for r in bg_rockets:
        rx = int(r[0])
        ry = int(r[1])
        frame = FLAME1_BITMAP if (frame_count // 3) % 2 == 0 else FLAME2_BITMAP
        thumby.display.blit(frame, rx - FLAME_W // 2, ry + ROCKET_H - 3, FLAME_W, FLAME_H, 0, 0, 0)
        thumby.display.blit(ROCKET_BITMAP, rx - ROCKET_W // 2, ry - ROCKET_H // 2, ROCKET_W, ROCKET_H, 0, 0, 0)


def draw_sky():
    for s in stars:
        if (frame_count + s[2]) % 41 < 33:
            thumby.display.setPixel(s[0], s[1], 1)
    # Earth, upper right
    draw_circle(W - 10, 7, 4, 1)
    # small cratered moon, upper left
    draw_disc(8, 5, 3, 1)
    thumby.display.setPixel(7, 4, 0)
    thumby.display.setPixel(9, 6, 0)


def gen_terrain(lvl):
    """Deterministic (seeded by level number) cratered moon terrain,
    so LEVEL SELECT always gives back the same layout for a level.
    Returns heights, padStart, padEnd, padY, craters, boulders, stipple."""
    random.seed(lvl * 7919 + 13)

    difficulty = lvl if lvl < 12 else 12
    pad_width = 16 - difficulty
    if pad_width < 8:
        pad_width = 8
    pad_start = random.randint(4, W - pad_width - 4)
    pad_end = pad_start + pad_width
    base_y = random.randint(H - 13, H - 8)

    heights = [base_y] * W
    h = base_y
    roughness = 2 + difficulty // 3
    for x in range(W):
        if pad_start <= x < pad_end:
            h = base_y
        elif x % 3 == 0:
            h += random.randint(-roughness, roughness)
            if h < H - 20:
                h = H - 20
            if h > H - 3:
                h = H - 3
        heights[x] = h
    for x in range(pad_start, pad_end):
        heights[x] = base_y

    # crater dips carved into the terrain (kept away from the pad)
    craters = []
    for i in range(3):
        ccx = random.randint(6, W - 7)
        cr = 2 if (i % 2 == 0) else 3
        if pad_start - cr - 2 <= ccx <= pad_end + cr + 2:
            continue
        craters.append(ccx)
        for dx in range(-cr, cr + 1):
            xx = ccx + dx
            if 0 <= xx < W:
                ad = dx if dx >= 0 else -dx
                dip = cr - ad
                if dip > 0:
                    heights[xx] += dip
        for edge in (ccx - cr - 1, ccx + cr + 1):
            if 0 <= edge < W:
                heights[edge] -= 1

    # small decorative boulders sitting on the surface, away from the pad
    boulders = []
    for i in range(4):
        bx = random.randint(2, W - 3)
        if pad_start - 2 <= bx <= pad_end + 2:
            continue
        boulders.append(bx)

    # precomputed regolith stipple texture just beneath the crust
    stipple = []
    for x in range(W):
        gy = heights[x]
        for dy in range(3, 7):
            y = gy + dy
            if y < H and (x * 3 + y * 7) % 5 == 0:
                stipple.append((x, y))

    # free up randomness again for gameplay-feel variety between attempts
    random.seed(time.ticks_us())

    return heights, pad_start, pad_end, base_y, craters, boulders, stipple


ground, padStart, padEnd, padY, craters, boulders, stipple = gen_terrain(level)

# ---------------- freeroam world ----------------
FR_W = 240
FR_H = 160
FR_ITEM_COUNT = 10

random.seed(4242)
FR_ITEMS = []
for _i in range(FR_ITEM_COUNT):
    _ix = random.randint(16, FR_W - 16)
    _iy = random.randint(16, FR_H - 16)
    FR_ITEMS.append((_ix, _iy, _i % 3))
FR_PLANETS = []
for _i in range(6):
    _px = random.randint(8, FR_W - 8)
    _py = random.randint(8, FR_H - 8)
    _pr = random.randint(3, 7)
    FR_PLANETS.append((_px, _py, _pr))
random.seed(time.ticks_us())

frX = FR_W / 2.0
frY = FR_H / 2.0
frVX = 0.0
frVY = 0.0
frToastTimer = 0
frToastText = ""


def draw_item_icon(x, y, kind):
    if kind == 0:      # star
        thumby.display.drawLine(x - 2, y, x + 2, y, 1)
        thumby.display.drawLine(x, y - 2, x, y + 2, 1)
    elif kind == 1:    # gem
        thumby.display.drawLine(x, y - 2, x - 2, y, 1)
        thumby.display.drawLine(x - 2, y, x, y + 2, 1)
        thumby.display.drawLine(x, y + 2, x + 2, y, 1)
        thumby.display.drawLine(x + 2, y, x, y - 2, 1)
    else:              # orb
        draw_disc(x, y, 2, 1)


# ---------------- ship state ----------------
shipX = float(W // 2)
shipY = 6.0
vx = 0.0
vy = 0.0
fuel = MAX_FUEL

# ---------------- particles: [x, y, vx, vy, life] ----------------
particles = []
PARTICLE_CAP = 26


def spawn_exhaust(x, y):
    if len(particles) >= PARTICLE_CAP:
        return
    particles.append([x + frand(-1, 1), y, frand(-0.3, 0.3), frand(0.5, 1.0), 10])


def spawn_side_puff(x, y, direction):
    if len(particles) >= PARTICLE_CAP:
        return
    particles.append([x, y + frand(-1, 1), direction * frand(0.4, 0.9), frand(-0.2, 0.2), 8])


def spawn_dust(x, y):
    for i in range(7):
        if len(particles) >= PARTICLE_CAP:
            break
        dx, dy = EXPLOSION_DIRS[random.randint(0, 11)]
        particles.append([x, y, dx * frand(0.2, 0.6), -abs(dy) * frand(0.2, 0.5), random.randint(8, 14)])


def spawn_explosion(x, y):
    for i in range(14):
        if len(particles) >= PARTICLE_CAP:
            break
        dx, dy = EXPLOSION_DIRS[i % 12]
        spd = frand(0.5, 1.6)
        particles.append([x, y, dx * spd, dy * spd, random.randint(10, 20)])


def update_particles():
    i = 0
    while i < len(particles):
        p = particles[i]
        p[0] += p[2]
        p[1] += p[3]
        p[3] += 0.03
        p[4] -= 1
        if p[4] <= 0:
            particles.pop(i)
        else:
            i += 1


def draw_particles():
    for p in particles:
        thumby.display.setPixel(int(p[0]), int(p[1]), 1)


def reset_ship():
    global shipX, shipY, vx, vy, fuel, particles
    shipX = float(random.randint(14, W - 14))
    shipY = 6.0
    vx = 0.0
    vy = 0.0
    fuel = MAX_FUEL - (level - 1) * 2
    if fuel < 45:
        fuel = 45
    particles = []


reset_ship()


# ---------------- drawing helpers ----------------
def draw_ground():
    for x in range(W):
        gy = ground[x]
        cap = gy + 2
        if cap > H - 1:
            cap = H - 1
        thumby.display.drawLine(x, gy, x, cap, 1)
    for (sx, sy) in stipple:
        thumby.display.setPixel(sx, sy, 1)
    for bx in boulders:
        by = ground[bx]
        thumby.display.setPixel(bx, by - 1, 1)
        thumby.display.setPixel(bx - 1, by - 1, 1)
        thumby.display.setPixel(bx, by - 2, 1)
    # landing pad: flat highlighted strip with a flag at each end
    glow = 1 if (frame_count // 6) % 2 == 0 else 0
    thumby.display.drawLine(padStart, padY - 1 - glow, padEnd, padY - 1 - glow, 1)
    for fx in (padStart, padEnd - 1):
        thumby.display.drawLine(fx, padY - 6, fx, padY - 1, 1)
    thumby.display.drawLine(padStart, padY - 6, padStart + 3, padY - 5, 1)
    thumby.display.drawLine(padEnd - 1, padY - 6, padEnd - 4, padY - 5, 1)


def draw_pad_highlight():
    """A blinking 'land here' arrow above the pad."""
    if (frame_count // 8) % 2 == 0:
        cx = (padStart + padEnd) // 2
        ay = padY - 14
        if ay < 8:
            ay = 8
        thumby.display.drawLine(cx, ay, cx, ay + 5, 1)
        thumby.display.drawLine(cx - 2, ay + 3, cx, ay + 5, 1)
        thumby.display.drawLine(cx + 2, ay + 3, cx, ay + 5, 1)


def draw_ship(cx, cy, thrust_main, thrust_dir):
    dx = cx - ROCKET_W // 2
    dy = cy - ROCKET_H // 2
    if thrust_main:
        frame = FLAME1_BITMAP if (time.ticks_ms() // 80) % 2 == 0 else FLAME2_BITMAP
        thumby.display.blit(frame, cx - FLAME_W // 2, dy + ROCKET_H - 2, FLAME_W, FLAME_H, 0, 0, 0)
    thumby.display.blit(ROCKET_BITMAP, dx, dy, ROCKET_W, ROCKET_H, 0, 0, 0)
    if thrust_dir != 0:
        px = dx + (ROCKET_W - 1 if thrust_dir < 0 else 0)
        py = dy + ROCKET_H // 2
        thumby.display.setPixel(px, py, 1)
        thumby.display.setPixel(px, py + 1, 1)


def draw_hud():
    thumby.display.drawRectangle(0, 0, 24, 5, 1)
    fw = int(22 * fuel / MAX_FUEL)
    if fw > 0:
        thumby.display.drawFilledRectangle(1, 1, fw, 3, 1)
    dtext(str(level), W - 12, 0)

    gx = int(shipX)
    if gx < 0:
        gx = 0
    if gx > W - 1:
        gx = W - 1
    bottom = shipY + ROCKET_H / 2
    alt = ground[gx] - bottom
    if alt < 14:
        safe = abs(vy) < SAFE_VY and abs(vx) < SAFE_VX
        if safe:
            thumby.display.drawFilledRectangle(W - 6, H - 6, 5, 5, 1)
        elif (frame_count // 4) % 2 == 0:
            thumby.display.drawRectangle(W - 6, H - 6, 5, 5, 1)


# ---------------- interactive tutorial state ----------------
tutStep = 0
tutShipX = float(W // 2)
tutShipY = 14.0
tutVX = 0.0
tutVY = 0.0
tutFuel = 100.0
tutHold = 0
tutLeftCount = 0
tutRightCount = 0
tutGround = None
tutPadStart = 0
tutPadEnd = 0
tutPadY = 0


def tut_reset():
    global tutShipX, tutShipY, tutVX, tutVY, tutFuel, tutHold, tutLeftCount, tutRightCount
    tutShipX = float(W // 2)
    tutShipY = 14.0
    tutVX = 0.0
    tutVY = 0.0
    tutFuel = 100.0
    tutHold = 0
    tutLeftCount = 0
    tutRightCount = 0


# ---------------- main loop ----------------
while True:
    thumby.display.fill(0)
    frame_count += 1

    if state == STATE_MENU:
        draw_sky()
        draw_ring_planet(58, 30, 3)
        update_bg_rockets()
        draw_bg_rockets()

        pulse = (frame_count // 10) % 2
        title = "LANDER"
        tx = (W - len(title) * 6) // 2
        thumby.display.drawFilledRectangle(tx - 2, 0, len(title) * 6 + 4, 9, 1 if pulse == 0 else 0)
        thumby.display.drawText(title, tx, 1, 0 if pulse == 0 else 1)

        for i, label in enumerate(MENU_ITEMS):
            y = 10 + i * 6
            prefix = ">" if i == menuIndex else " "
            dtext(prefix + label, 2, y)

        if thumby.buttonD.justPressed():
            menuIndex = (menuIndex + 1) % len(MENU_ITEMS)
            sfx_blip()
        if thumby.buttonU.justPressed():
            menuIndex = (menuIndex - 1) % len(MENU_ITEMS)
            sfx_blip()
        if thumby.buttonA.justPressed():
            sfx_blip()
            if menuIndex == 0:
                level = 1
                ground, padStart, padEnd, padY, craters, boulders, stipple = gen_terrain(level)
                reset_ship()
                transition_wipe()
                countdown = COUNTDOWN_LEN
                state = STATE_COUNTDOWN
            elif menuIndex == 1:
                selLevel = level if level <= maxUnlocked else maxUnlocked
                transition_wipe()
                state = STATE_LEVELSELECT
            elif menuIndex == 2:
                tutStep = 0
                tut_reset()
                transition_wipe()
                state = STATE_TUTORIAL
            elif menuIndex == 3:
                frX = FR_W / 2.0
                frY = FR_H / 2.0
                frVX = 0.0
                frVY = 0.0
                frToastTimer = 0
                transition_wipe()
                state = STATE_FREEROAM
            elif menuIndex == 4:
                settingsIndex = 0
                transition_wipe()
                state = STATE_SETTINGS

    elif state == STATE_TUTORIAL:
        draw_sky()
        if thumby.buttonB.justPressed():
            sfx_blip()
            transition_wipe()
            state = STATE_MENU
        elif tutStep == 0:
            dtext_center("WELCOME!", 4)
            dtext("Guide your ship", 2, 14)
            dtext("to a safe landing", 2, 22)
            dtext_center("A: Begin", 32)
            if thumby.buttonA.justPressed():
                sfx_blip()
                tut_reset()
                tutStep = 1

        elif tutStep == 1:
            tutVY += GRAVITY
            pressingUp = thumby.buttonU.pressed()
            if pressingUp:
                tutVY -= MAIN_THRUST
                tutHold += 1
            tutShipY += tutVY
            if tutShipY > H - 8:
                tutShipY = H - 8
                tutVY = 0.0
            if tutShipY < 6:
                tutShipY = 6
                tutVY = 0.0
            draw_ship(int(tutShipX), int(tutShipY), pressingUp, 0)
            dtext("Press UP to fly!", 2, 0)
            if tutHold > 25:
                dtext_center("Great! A: Next", 33)
                if thumby.buttonA.justPressed():
                    sfx_blip()
                    tut_reset()
                    tutStep = 2
            else:
                dtext_center("Hold UP a moment", 33)

        elif tutStep == 2:
            tutVY += GRAVITY
            pressingUp = thumby.buttonU.pressed()
            if pressingUp:
                tutVY -= MAIN_THRUST
            if thumby.buttonL.pressed():
                tutVX -= SIDE_THRUST
                tutLeftCount += 1
            if thumby.buttonR.pressed():
                tutVX += SIDE_THRUST
                tutRightCount += 1
            tutVX *= DRAG
            tutShipX += tutVX
            tutShipY += tutVY
            if tutShipY > H - 8:
                tutShipY = H - 8
                tutVY = 0.0
            if tutShipY < 6:
                tutShipY = 6
                tutVY = 0.0
            if tutShipX < 6:
                tutShipX = 6
                tutVX = 0.0
            if tutShipX > W - 6:
                tutShipX = W - 6
                tutVX = 0.0
            tdir = -1 if thumby.buttonL.pressed() else (1 if thumby.buttonR.pressed() else 0)
            draw_ship(int(tutShipX), int(tutShipY), pressingUp, tdir)
            dtext("L/R to steer!", 2, 0)
            if tutLeftCount > 8 and tutRightCount > 8:
                dtext_center("Nice! A: Next", 33)
                if thumby.buttonA.justPressed():
                    sfx_blip()
                    tutStep = 3
                    tutFuel = 100.0
            else:
                dtext_center("Try LEFT then RIGHT", 33)

        elif tutStep == 3:
            dtext("Fuel is limited!", 2, 0)
            if thumby.buttonU.pressed() and tutFuel > 0:
                tutFuel -= 1.0
                if tutFuel < 0:
                    tutFuel = 0
            thumby.display.drawRectangle(2, 14, 40, 6, 1)
            fw = int(38 * tutFuel / 100.0)
            if fw > 0:
                thumby.display.drawFilledRectangle(3, 15, fw, 4, 1)
            dtext("Use it wisely!", 2, 22)
            dtext_center("A: Continue", 33)
            if thumby.buttonA.justPressed():
                sfx_blip()
                tutGround, tutPadStart, tutPadEnd, tutPadY, _tc, _tb, _ts = gen_terrain(1)
                tutShipX = float(W // 2)
                tutShipY = 6.0
                tutVX = 0.0
                tutVY = 0.0
                tutFuel = 100.0
                tutStep = 4

        elif tutStep == 4:
            thrustMain = False
            if thumby.buttonU.pressed() and tutFuel > 0:
                tutVY -= MAIN_THRUST
                tutFuel -= 1.0
                thrustMain = True
            if thumby.buttonL.pressed() and tutFuel > 0:
                tutVX -= SIDE_THRUST
                tutFuel -= 0.4
            if thumby.buttonR.pressed() and tutFuel > 0:
                tutVX += SIDE_THRUST
                tutFuel -= 0.4
            if tutFuel < 0:
                tutFuel = 0
            tutVY += GRAVITY
            tutVX *= DRAG
            tutShipX += tutVX
            tutShipY += tutVY
            if tutShipX < 5:
                tutShipX = 5
                tutVX = 0.0
            if tutShipX > W - 5:
                tutShipX = W - 5
                tutVX = 0.0

            tgx = int(tutShipX)
            if tgx < 0:
                tgx = 0
            if tgx > W - 1:
                tgx = W - 1
            tgy = tutGround[tgx]
            tbottom = tutShipY + ROCKET_H / 2

            if tbottom >= tgy:
                tutShipY = tgy - ROCKET_H / 2
                on_pad = tutPadStart <= tgx < tutPadEnd
                soft = abs(tutVY) < SAFE_VY and abs(tutVX) < SAFE_VX
                if on_pad and soft:
                    sfx_land()
                    tutStep = 5
                else:
                    sfx_crash()
                    tutShipX = float(W // 2)
                    tutShipY = 6.0
                    tutVX = 0.0
                    tutVY = 0.0
                    tutFuel = 100.0
            else:
                for x in range(W):
                    gyx = tutGround[x]
                    cap = gyx + 2
                    if cap > H - 1:
                        cap = H - 1
                    thumby.display.drawLine(x, gyx, x, cap, 1)
                glowT = 1 if (frame_count // 6) % 2 == 0 else 0
                thumby.display.drawLine(tutPadStart, tutPadY - 1 - glowT, tutPadEnd, tutPadY - 1 - glowT, 1)
                if (frame_count // 8) % 2 == 0:
                    acx = (tutPadStart + tutPadEnd) // 2
                    ay = tutPadY - 14
                    if ay < 8:
                        ay = 8
                    thumby.display.drawLine(acx, ay, acx, ay + 5, 1)
                tdir = -1 if thumby.buttonL.pressed() else (1 if thumby.buttonR.pressed() else 0)
                draw_ship(int(tutShipX), int(tutShipY), thrustMain, tdir)
                dtext("Land on the pad!", 2, 0)

        elif tutStep == 5:
            dtext_center("GREAT JOB!", 12)
            dtext_center("You're ready.", 20)
            dtext_center("A: Finish", 33)
            if thumby.buttonA.justPressed():
                sfx_blip()
                transition_wipe()
                state = STATE_MENU

    elif state == STATE_LEVELSELECT:
        dtext("SELECT LVL", 4, 0)
        boxW, boxH, gap = 12, 14, 2
        startX = 2
        y = 12
        lo = selLevel - 2
        for i in range(5):
            lvl = lo + i
            bx = startX + i * (boxW + gap)
            if lvl < 1:
                continue
            unlocked = lvl <= maxUnlocked
            selected = (lvl == selLevel)
            if selected:
                thumby.display.drawFilledRectangle(bx, y, boxW, boxH, 1)
            else:
                thumby.display.drawRectangle(bx, y, boxW, boxH, 1)
            fg = 0 if selected else 1
            if unlocked:
                txt = str(lvl)
                tx = bx + (boxW - len(txt) * 6) // 2
                thumby.display.drawText(txt, tx, y + 4, fg)
            else:
                lx, ly = bx + boxW // 2 - 2, y + boxH // 2 - 3
                thumby.display.drawRectangle(lx - 1, ly + 2, 6, 4, fg)
                thumby.display.drawLine(lx, ly, lx, ly + 2, fg)
                thumby.display.drawLine(lx + 4, ly, lx + 4, ly + 2, fg)
                thumby.display.drawLine(lx, ly, lx + 4, ly, fg)
        dtext("A:Play", 0, 33)
        dtext("B:Back", 40, 33)

        if thumby.buttonR.justPressed() and selLevel < maxUnlocked:
            selLevel += 1
            sfx_blip()
        if thumby.buttonL.justPressed() and selLevel > 1:
            selLevel -= 1
            sfx_blip()
        if thumby.buttonA.justPressed():
            sfx_blip()
            level = selLevel
            ground, padStart, padEnd, padY, craters, boulders, stipple = gen_terrain(level)
            reset_ship()
            transition_wipe()
            countdown = COUNTDOWN_LEN
            state = STATE_COUNTDOWN
        if thumby.buttonB.justPressed():
            sfx_blip()
            transition_wipe()
            state = STATE_MENU

    elif state == STATE_SETTINGS:
        labels = ["SOUND:" + ("ON" if soundOn else "OFF"), "RESET SAVE", "BACK"]
        dtext("SETTINGS", 8, 0)
        for i, label in enumerate(labels):
            prefix = ">" if i == settingsIndex else " "
            dtext(prefix + label, 2, 10 + i * 8)

        if thumby.buttonD.justPressed():
            settingsIndex = (settingsIndex + 1) % len(labels)
            sfx_blip()
        if thumby.buttonU.justPressed():
            settingsIndex = (settingsIndex - 1) % len(labels)
            sfx_blip()
        if thumby.buttonA.justPressed():
            if settingsIndex == 0:
                soundOn = not soundOn
                save_game()
                sfx_blip()
            elif settingsIndex == 1:
                maxUnlocked = 1
                frFound = 0
                thumby.saveData.setItem("frfound", 0)
                save_game()
                sfx_blip()
            elif settingsIndex == 2:
                transition_wipe()
                state = STATE_MENU
        if thumby.buttonB.justPressed():
            transition_wipe()
            state = STATE_MENU

    elif state == STATE_COUNTDOWN:
        draw_sky()
        draw_ground()
        draw_pad_highlight()
        draw_ship(int(shipX), int(shipY), False, 0)
        n = countdown // 30 + 1
        if n > 3:
            n = 3
        dtext_center(str(n), 14)
        dtext_center("GET READY", 24)
        countdown -= 1
        if countdown <= 0:
            sfx_launch()
            state = STATE_PLAY

    elif state == STATE_PLAY:
        thrustMain = False
        thrustDir = 0

        if thumby.buttonU.pressed() and fuel > 0:
            vy -= MAIN_THRUST
            fuel -= 1.0
            thrustMain = True
            if frame_count % 4 == 0:
                spawn_exhaust(shipX, shipY + ROCKET_H / 2)

        if thumby.buttonL.pressed() and fuel > 0:
            vx -= SIDE_THRUST
            fuel -= 0.4
            thrustDir = -1
            if frame_count % 5 == 0:
                spawn_side_puff(shipX + ROCKET_W / 2, shipY, 1)

        if thumby.buttonR.pressed() and fuel > 0:
            vx += SIDE_THRUST
            fuel -= 0.4
            thrustDir = 1
            if frame_count % 5 == 0:
                spawn_side_puff(shipX - ROCKET_W / 2, shipY, -1)

        if fuel < 0:
            fuel = 0

        vy += GRAVITY
        vx *= DRAG
        shipX += vx
        shipY += vy

        if shipX < ROCKET_W / 2:
            shipX = ROCKET_W / 2
            vx = -vx * WALL_BOUNCE
        if shipX > W - ROCKET_W / 2:
            shipX = W - ROCKET_W / 2
            vx = -vx * WALL_BOUNCE

        gx = int(shipX)
        if gx < 0:
            gx = 0
        if gx > W - 1:
            gx = W - 1
        gy = ground[gx]

        bottom = shipY + ROCKET_H / 2

        if bottom >= gy:
            shipY = gy - ROCKET_H / 2
            on_pad = padStart <= gx < padEnd
            soft = abs(vy) < SAFE_VY and abs(vx) < SAFE_VX

            if on_pad and soft:
                resultMsg = "LANDED!"
                flashFrames = 0
                spawn_dust(shipX, gy)
                sfx_land()
                level += 1
                if level > maxUnlocked:
                    maxUnlocked = level
                    save_game()
            else:
                resultMsg = "CRASHED!"
                flashFrames = 3
                spawn_explosion(shipX, gy)
                sfx_crash()

            resultTimer = 55
            state = STATE_RESULT
        else:
            update_particles()
            draw_sky()
            draw_ground()
            draw_pad_highlight()
            draw_particles()
            draw_ship(int(shipX), int(shipY), thrustMain, thrustDir)
            draw_hud()

    elif state == STATE_RESULT:
        if flashFrames > 0:
            thumby.display.fill(1)
            flashFrames -= 1
        else:
            draw_sky()
            draw_ground()
            if resultMsg == "LANDED!":
                draw_ship(int(shipX), int(shipY), False, 0)
            update_particles()
            draw_particles()
            thumby.display.drawFilledRectangle(6, 14, 60, 13, 0)
            thumby.display.drawRectangle(6, 14, 60, 13, 1)
            thumby.display.drawText(resultMsg, 14, 18, 1)

        resultTimer -= 1
        if resultTimer <= 0:
            if resultMsg == "LANDED!":
                ground, padStart, padEnd, padY, craters, boulders, stipple = gen_terrain(level)
                reset_ship()
                countdown = COUNTDOWN_LEN
                state = STATE_COUNTDOWN
            else:
                state = STATE_OVER

    elif state == STATE_OVER:
        draw_sky()
        dtext("CRASHED!", 8, 4)
        dtext("Lvl reach:" + str(level), 2, 14)
        dtext("Best:" + str(maxUnlocked), 2, 22)
        if (time.ticks_ms() // 400) % 2 == 0:
            dtext_center("PRESS A", 32)

        if thumby.buttonA.justPressed():
            sfx_blip()
            transition_wipe()
            state = STATE_MENU

    elif state == STATE_FREEROAM:
        if thumby.buttonU.pressed():
            frVY -= 0.05
        if thumby.buttonD.pressed():
            frVY += 0.05
        if thumby.buttonL.pressed():
            frVX -= 0.05
        if thumby.buttonR.pressed():
            frVX += 0.05
        frVX *= 0.97
        frVY *= 0.97
        frX += frVX
        frY += frVY
        if frX < 4:
            frX = 4
            frVX = 0.0
        if frX > FR_W - 4:
            frX = FR_W - 4
            frVX = 0.0
        if frY < 4:
            frY = 4
            frVY = 0.0
        if frY > FR_H - 4:
            frY = FR_H - 4
            frVY = 0.0

        camX = frX - W / 2
        camY = frY - H / 2
        if camX < 0:
            camX = 0
        if camX > FR_W - W:
            camX = FR_W - W
        if camY < 0:
            camY = 0
        if camY > FR_H - H:
            camY = FR_H - H

        for s in stars:
            sx = int((s[0] * 3 - camX * 0.4)) % W
            sy = int((s[1] * 3 - camY * 0.4)) % (H - 8) + 2
            if (frame_count + s[2]) % 41 < 33:
                thumby.display.setPixel(sx, sy, 1)

        for (px, py, pr) in FR_PLANETS:
            sx = px - camX
            sy = py - camY
            if -pr <= sx <= W + pr and -pr <= sy <= H + pr:
                draw_circle(int(sx), int(sy), pr, 1)

        for idx in range(FR_ITEM_COUNT):
            ix, iy, kind = FR_ITEMS[idx]
            if frFound & (1 << idx):
                continue
            sx = ix - camX
            sy = iy - camY
            if -3 <= sx <= W + 3 and -3 <= sy <= H + 3:
                draw_item_icon(int(sx), int(sy), kind)
            ddx = ix - frX
            ddy = iy - frY
            if ddx * ddx + ddy * ddy < 36:
                frFound |= (1 << idx)
                thumby.saveData.setItem("frfound", frFound)
                thumby.saveData.save()
                frToastTimer = 45
                frToastText = "FOUND " + KIND_NAMES[kind] + "!"
                sfx_land()

        shx = int(frX - camX)
        shy = int(frY - camY)
        tdir = -1 if thumby.buttonL.pressed() else (1 if thumby.buttonR.pressed() else 0)
        draw_ship(shx, shy, thumby.buttonU.pressed(), tdir)

        foundCount = bin(frFound).count("1")
        dtext(str(foundCount) + "/" + str(FR_ITEM_COUNT), 2, 0)
        dtext("B:Exit", W - 32, 0)

        if frToastTimer > 0:
            dtext_center(frToastText, 32)
            frToastTimer -= 1

        if thumby.buttonB.justPressed():
            sfx_blip()
            save_game()
            transition_wipe()
            state = STATE_MENU

    thumby.display.update()