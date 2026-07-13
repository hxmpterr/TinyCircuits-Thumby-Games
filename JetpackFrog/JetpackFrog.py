from thumby import display, buttonA, buttonB, buttonL, buttonR
import time
import random

# --------------------
# Frog sprite (white body, transparent background)
# --------------------
FrogSprite = bytearray([0,0,92,34,34,92,0,0])
FROG_COLOR = 0  # white

# --------------------
# Constants
# --------------------
PIPE_HEIGHT = 4
PIPE_GAP = 24
PIPE_SPEED = 1   # slower
PIPE_SPACING = 36  # vertical distance between pipes

# --------------------
# Helper functions
# --------------------
def draw_title():
    display.fill(0)
    display.drawText("Jetpack frog", 0, 0, 1)
    display.drawText("A to start", 8, 32, 1)
    display.blit(FrogSprite, 28, 14, 8, 8, FROG_COLOR, 0, 0)
    display.update()

def draw_game_over(score):
    display.fill(0)
    display.drawText("YOU DIED", 4, 0, 1)
    display.drawText(f"SC:{score}", 0, 16, 1)
    display.drawText("A: @ B: X", 0, 32, 1)
    display.update()

def spawn_pipe():
    gap_x = random.randint(4, display.width - PIPE_GAP - 4)
    pipes.append([-PIPE_HEIGHT, gap_x])

# --------------------
# Title Screen
# --------------------
draw_title()
while not buttonA.pressed():
    time.sleep(0.01)

# --------------------
# Main Game Loop
# --------------------
def game_loop():
    global pipes
    frog_x = 28
    frog_y = 30
    frog_dir = 0

    score = 0
    pipes = []
    spawn_pipe()

    while True:
        display.fill(0)

        # ---- Input (sticky left/right)
        if buttonR.pressed():
            frog_dir = 1
        elif buttonL.pressed():
            frog_dir = -1

        frog_x += frog_dir
        frog_x = max(0, min(frog_x, display.width - 8))

        # ---- Pipes (background)
        for pipe in pipes:
            pipe[0] += PIPE_SPEED
            y = pipe[0]
            gap_x = pipe[1]

            # Left segment
            display.drawFilledRectangle(0, y, gap_x, PIPE_HEIGHT, 1)
            # Right segment
            display.drawFilledRectangle(gap_x + PIPE_GAP, y, display.width - (gap_x + PIPE_GAP), PIPE_HEIGHT, 1)

        # Remove offscreen pipes
        pipes = [p for p in pipes if p[0] < display.height]

        # Spawn new pipes with spacing
        if len(pipes) == 0 or pipes[-1][0] > PIPE_SPACING:
            spawn_pipe()

        # ---- Frog (foreground, white)
        display.blit(FrogSprite, frog_x, frog_y, 8, 8, FROG_COLOR, 0, 0)

        # ---- Score HUD
        display.drawText(f"SC:{score}", 0, 0, 1)

        display.update()
        time.sleep(0.03)

        # ---- Collision check
        for pipe in pipes:
            y = pipe[0]
            gap_x = pipe[1]

            if frog_y < y + PIPE_HEIGHT and frog_y + 8 > y:
                if frog_x < gap_x or frog_x + 8 > gap_x + PIPE_GAP:
                    return score  # game over

        # Increment score
        score += 1

# --------------------
# Game Manager
# --------------------
while True:
    score = game_loop()

    # Show You Died screen
    draw_game_over(score)

    # Wait for A or B
    while True:
        if buttonA.pressed():
            break  # restart game
        if buttonB.pressed():
            draw_title()
            while not buttonA.pressed():
                time.sleep(0.01)
            break  # back to game
        time.sleep(0.01)
