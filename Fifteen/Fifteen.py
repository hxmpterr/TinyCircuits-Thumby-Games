import thumby
import time
import random

random.seed(time.ticks_ms())

SIZE = 4
CELL_W = 18
CELL_H = 10
FRAMES = 7

SCREEN_W = 72
SCREEN_H = 40

offset_x = (SCREEN_W - (SIZE * CELL_W))
offset_y = (SCREEN_H - (SIZE * CELL_H))


def show_start_screen():

    frame = 0
    last_empty_pos = -1

    while True:

        thumby.display.fill(0)

        # --- TITLE ---
        thumby.display.drawText("Fifteen", 15, 2, 1)

        # --- MINI PUZZLE ---
        mini_y = 14

        positions = [3, 2, 1, 0, 1, 2]
        empty_pos = positions[(frame // 120) % len(positions)]

        if empty_pos != last_empty_pos:
            thumby.audio.play(1200, 20)
            last_empty_pos = empty_pos

        for i in range(4):

            x = 18 + i * 9

            thumby.display.drawRectangle(x, mini_y, 8, 8, 1)

            if i == empty_pos:
                continue

            if i < empty_pos:
                number = str(i + 1)
            else:
                number = str(i)

            thumby.display.drawText(number, x + 2, mini_y + 1, 1)

        # --- MENU ---
        thumby.display.drawText("A Start", 15, 24, 1)
        thumby.display.drawText("B Reset", 15, 32, 1)

        thumby.display.update()

        frame = (frame + 1) % 720

        if thumby.buttonA.justPressed():
            return


def play_win_sound():

    thumby.audio.playBlocking(1047, 80)
    thumby.audio.playBlocking(1319, 80)
    thumby.audio.playBlocking(1568, 80)
    thumby.audio.playBlocking(2093, 200)


def is_solved(grid):

    expected = 0

    for y in range(SIZE):
        for x in range(SIZE):
            if grid[y][x] != expected:
                return False
            expected += 1

    return True


def find_empty(grid):

    for y in range(SIZE):
        for x in range(SIZE):
            if grid[y][x] == 15:
                return x, y

    return None, None


def generate_board(min_moves=175, max_moves=225):

    moves = random.randint(min_moves, max_moves)

    grid = [
        [0, 1, 2, 3],
        [4, 5, 6, 7],
        [8, 9, 10, 11],
        [12, 13, 14, 15]
    ]

    ex = 3
    ey = 3

    for _ in range(moves):

        options = []

        if ex > 0:
            options.append((-1, 0))
        if ex < 3:
            options.append((1, 0))
        if ey > 0:
            options.append((0, -1))
        if ey < 3:
            options.append((0, 1))

        dx, dy = random.choice(options)

        nx = ex + dx
        ny = ey + dy

        grid[ey][ex], grid[ny][nx] = grid[ny][nx], grid[ey][ex]

        ex = nx
        ey = ny

    return grid


def draw(grid, anim=None):

    thumby.display.fill(0)

    for y in range(SIZE):
        for x in range(SIZE):

            if anim and x == anim["from_x"] and y == anim["from_y"]:
                continue

            px = offset_x + x * CELL_W
            py = offset_y + y * CELL_H

            thumby.display.drawRectangle(px, py, CELL_W, CELL_H, 1)

            value = grid[y][x]

            if value != 15:

                text = str(value + 1)

                tx = px + (7 if len(text) == 1 else 4)
                ty = py + 2

                thumby.display.drawText(text, tx, ty, 1)

    if anim:

        fx = offset_x + anim["from_x"] * CELL_W
        fy = offset_y + anim["from_y"] * CELL_H

        tx0 = offset_x + anim["to_x"] * CELL_W
        ty0 = offset_y + anim["to_y"] * CELL_H

        progress = anim["progress"]

        px = int(fx + (tx0 - fx) * progress)
        py = int(fy + (ty0 - fy) * progress)

        text = str(anim["value"] + 1)

        thumby.display.drawRectangle(px, py, CELL_W, CELL_H, 1)

        text_x = px + (7 if len(text) == 1 else 4)
        text_y = py + 2

        thumby.display.drawText(text, text_x, text_y, 1)

    thumby.display.update()


def move_tile(grid, dx, dy):

    ex, ey = find_empty(grid)

    tx = ex + dx
    ty = ey + dy

    if tx < 0 or tx >= SIZE or ty < 0 or ty >= SIZE:
        return False

    value = grid[ty][tx]

    thumby.audio.play(1200, 20)

    for frame in range(FRAMES + 1):

        draw(grid, {
            "from_x": tx,
            "from_y": ty,
            "to_x": ex,
            "to_y": ey,
            "value": value,
            "progress": frame / FRAMES
        })

    grid[ey][ex], grid[ty][tx] = grid[ty][tx], grid[ey][ex]

    return True


# ===== START =====
show_start_screen()

grid = generate_board()

game_won = False
moves = 0
best_moves = None


# ===== GAME LOOP =====
while True:

    # ===== WIN STATE =====
    if game_won:

        thumby.display.fill(0)
        thumby.display.drawText("WIN!", (72 - 4 * 5) // 2, 6, 1)
        
        
        text = "MOVES: " + str(moves)
        x = (72 - len(text) * 5) // 2

        thumby.display.drawText(text, x, 18, 1)

        if best_moves is None or moves < best_moves:
            best_moves = moves
            thumby.display.drawText("NEW BEST!", (72 - 10 * 5) // 2, 28, 1)
        else:
            text = "BEST: " + str(best_moves)
            x = (72 - len(text) * 5) // 2

            thumby.display.drawText(text, x, 28, 1)

        thumby.display.update()

        if thumby.buttonA.justPressed():
            grid = generate_board()
            game_won = False
            moves = 0

        continue


    # ===== INPUT =====
    if thumby.buttonB.justPressed():
        grid = generate_board()
        game_won = False
        moves = 0

    if thumby.buttonL.justPressed():
        if move_tile(grid, -1, 0):
            moves += 1

    if thumby.buttonR.justPressed():
        if move_tile(grid, 1, 0):
            moves += 1

    if thumby.buttonU.justPressed():
        if move_tile(grid, 0, -1):
            moves += 1

    if thumby.buttonD.justPressed():
        if move_tile(grid, 0, 1):
            moves += 1


    # ===== CHECK WIN =====
    if is_solved(grid):
        game_won = True
        play_win_sound()
        continue


    draw(grid)