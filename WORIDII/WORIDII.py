import random, thumby


def load_images_data():
    file = open("/Games/WORIDII/WORIDII.bin", "rb")
    data = file.read()
    file.close()
    return bytearray(data)


data = load_images_data()

broom = [
    thumby.Sprite(16, 16, data[0:32], 0, 0),
    thumby.Sprite(16, 16, data[32:64], 0, 0),
    thumby.Sprite(16, 16, data[64:96], 0, 0),
]
bug = thumby.Sprite(16, 8, data[96:112], 0, 0)
crate = thumby.Sprite(16, 16, data[112:144], 0, 0)
dpad = thumby.Sprite(8, 16, data[144:160], 4, 24)
heart = [
    thumby.Sprite(8, 8, data[160:168], 0, 0),
    thumby.Sprite(8, 8, data[168:176], 0, 0),
]
logo = thumby.Sprite(72, 24, data[176:392], 0, 0)
screen_game1 = thumby.Sprite(72, 24, data[392:608], 0, 0)
screen_game2 = thumby.Sprite(72, 24, data[608:824], 0, 0)
tile = [
    thumby.Sprite(40, 40, data[824:1024], 0, 0),
    thumby.Sprite(40, 40, data[1024:1224], 0, 0),
    thumby.Sprite(40, 40, data[1224:1424], 0, 0),
    thumby.Sprite(40, 40, data[1424:1624], 0, 0),
    thumby.Sprite(40, 40, data[1624:1824], 0, 0),
    thumby.Sprite(40, 40, data[1824:2024], 0, 0),
    thumby.Sprite(40, 40, data[2024:2224], 0, 0),
    thumby.Sprite(40, 40, data[2224:2424], 0, 0),
    thumby.Sprite(40, 40, data[2424:2624], 0, 0),
    thumby.Sprite(40, 40, data[2624:2824], 0, 0),
    thumby.Sprite(40, 40, data[2824:3024], 0, 0),
    thumby.Sprite(40, 40, data[3024:3224], 0, 0),
]
wrong = thumby.Sprite(16, 16, data[3224:3256], 0, 0)


def select_game(selected = 0):
    index = str(selected+1)
    games = [
        "Pairs",
        "Bug Run",
    ]
    max_selected = len(games)-1
    thumby.display.setFont("/lib/font5x7.bin", 5, 7, 1)
    while(1):
        thumby.display.fill(0)
        thumby.display.drawSprite(logo)
        thumby.display.drawSprite(dpad)
        thumby.display.drawText(index, 16, 28, 1)
        thumby.display.drawText(games[selected], 25, 28, 1)
        thumby.display.update()

        if thumby.buttonU.justPressed() and selected != 0:
            selected -= 1
            index = str(selected+1)
        if thumby.buttonD.justPressed() and selected != max_selected:
            selected += 1
            index = str(selected+1)
        if thumby.actionJustPressed():
            return selected


def pendulum(count):
    yield 0
    for i in range(1, count):
        yield i
        yield -i


class Game1:
    STATE_START = 0
    STATE_PLAYING = 1
    STATE_PICKED = 2
    STATE_WIN = 3

    # STATE_START
    START_1 = 0
    START_2 = 1

    # STATE_PICKED
    PICKED_FIRST = 0
    PICKED_WRONG = 1
    PICKED_CORRECT = 2

    # STATE_WIN
    WIN_A = 0
    WIN_B = 1
    WIN_BOTH = 2

    TILES_COLUMNS = 6
    TILES_ROWS = 4
    TILES_BOARD = TILES_COLUMNS*TILES_ROWS
    TILES_COUNT = TILES_BOARD//2
    TILE_NAMES = [
        "ARISTOCRATS",
        "TROLLS",
        "JARNI",
        "HISTORIAN",
        "ROB",
        "CHEECHA",
        "ESHA",
        "WORIDII",
        "MIGHTY BROOM",
        "JOURNAL",
        "CRATE",
        "TEAM QUADRIMUS",
    ]
    TILE_STATE_EMPTY = 0
    TILE_STATE_FULL = 1
    TILE_STATE_PICKED = 2
    TILE_STATE_SELECTED_A = 3
    TILE_STATE_SELECTED_B = 4


    def __init__(self):
        self.state = self.STATE_START
        self.substate = self.START_1
        self.tiles = [x for x in range(self.TILES_COUNT) for _ in range(2)] # values of all tiles on screen
        self.tiles_picked = [0 for _ in range(self.TILES_BOARD)]            # 0 for available tiles, 1 for picked tiles
        self.player = 0                                                     # currently playing player, 0 for A, 1 for B
        self.players = 2                                                    # players count, only 1 or 2
        self.score = [0, 0]
        self.score_text = ["00", "00"]
        self.selected = 0 # index of selected tile, useable for tiles and tiles_picked lists
        self.picked = -1  # index of currently picked tile, the first of the pair
        self.scroll_x = 0 # applied to STATE_PICKED_* screens


    def shuffle_tiles(self):
        random.seed()
        length = len(self.tiles)
        for _ in range(length*4):
            a = random.randint(0, length-1)
            b = random.randint(0, length-1)
            self.tiles[a], self.tiles[b] = self.tiles[b], self.tiles[a]


    def set_score(self, player, score):
        self.score[player] = score
        self.score_text[player] = "{:02d}".format(score)


    def increment_score(self, player):
        self.set_score(player, self.score[player]+1)


    def reset(self):
        self.state = self.STATE_START
        self.substate = self.START_1
        self.shuffle_tiles()
        for i in range(len(self.tiles_picked)):
            self.tiles_picked[i] = 0
        self.player = 0
        self.set_score(0, 0)
        self.set_score(1, 0)
        self.selected = 0
        self.picked = -1
        self.scroll_x = 0


    def start(self):
        thumby.display.setFont("/lib/font3x5.bin", 3, 5, 1)

        self.reset()

        frame = 0
        while(1):
            frame += 1
            if self.process(frame):
                return


    def draw_tile(self, x, y, state = 0):
        if state == self.TILE_STATE_EMPTY:
            return
        x = x*9+3
        y = y*9+3
        if state == self.TILE_STATE_FULL:
            thumby.display.drawFilledRectangle(x, y, 7, 7, 1)
        elif state == self.TILE_STATE_PICKED:
            thumby.display.drawRectangle(x, y, 7, 7, 1)
        else:
            thumby.display.drawFilledRectangle(x, y, 7, 7, 1)
            thumby.display.drawText("A" if state == self.TILE_STATE_SELECTED_A else "B", x+2, y+1, 0)


    def draw_player(self, x, y, name, score, selected = False):
        if selected:
            thumby.display.drawRectangle(x, y, 11, 16, 1)
        thumby.display.drawText(name, x+4, y+2, 1)
        thumby.display.drawText(score, x+2, y+9, 1)


    def tile_state(self, i):
        if self.picked == i:
            return self.TILE_STATE_PICKED
        if self.selected == i:
            return self.TILE_STATE_SELECTED_A if self.player == 0 else self.TILE_STATE_SELECTED_B
        return self.TILE_STATE_EMPTY if self.tiles_picked[i] else self.TILE_STATE_FULL


    def try_select(self, i):
        if i < 0 or i >= self.TILES_BOARD:
            return False
        if self.picked == i or self.tiles_picked[i] != 0:
            return False
        self.selected = i
        return True


    def try_select_xy(self, x, y):
        if x < 0 or y < 0 or x >= self.TILES_COLUMNS or y >= self.TILES_ROWS:
            return False
        return self.try_select(y*self.TILES_COLUMNS+x)


    def move(self, delta_x, delta_y):
        x = self.selected % self.TILES_COLUMNS
        y = self.selected // self.TILES_COLUMNS
        if delta_x == 0: # vertical move
            for _ in range(self.TILES_ROWS):
                y += delta_y
                for d in pendulum(self.TILES_COLUMNS):
                    if self.try_select_xy(x+d, y):
                        return
        else: # horizontal move
            for _ in range(self.TILES_COLUMNS):
                x += delta_x
                for d in pendulum(self.TILES_ROWS):
                    if self.try_select_xy(x, y+d):
                        return


    def select_first_available(self):
        for i in range(1, self.TILES_BOARD):
            if self.try_select((self.selected+i) % self.TILES_BOARD):
                return


    def pick(self):
        if self.picked < 0:
            self.picked = self.selected
            self.state = self.STATE_PICKED
            self.substate = self.PICKED_FIRST
            return
        first = self.tiles[self.picked]
        second = self.tiles[self.selected]
        if first == second:
            self.increment_score(self.player)
            self.tiles_picked[self.picked] = 1
            self.tiles_picked[self.selected] = 1
            self.state = self.STATE_PICKED
            self.substate = self.PICKED_CORRECT
        else:
            self.state = self.STATE_PICKED
            self.substate = self.PICKED_WRONG


    def check_win(self):
        if 0 in self.tiles_picked:
            return False
        self.state = self.STATE_WIN
        if self.score[0] == self.score[1]:
            self.substate = self.WIN_BOTH
        elif self.score[0] < self.score[1]:
            self.substate = self.WIN_B
        else:
            self.substate = self.WIN_A
        return True


    def draw_start(self):
        thumby.display.fill(0)

        thumby.display.drawSprite(screen_game1)

        thumby.display.drawText("Players:", 11, 28, 1)
        thumby.display.drawRectangle(45 if self.substate == self.START_1 else 55, 26, 7, 9, 1)
        thumby.display.drawText("1", 47, 28, 1)
        thumby.display.drawText("2", 57, 28, 1)

        thumby.display.update()


    def draw_tiles(self):
        thumby.display.fill(0)
        
        self.draw_player(58, 3, "A", self.score_text[0], self.player == 0)
        if self.players == 2:
            self.draw_player(58, 21, "B", self.score_text[1], self.player == 1)

        for y in range(self.TILES_ROWS):
            for x in range(self.TILES_COLUMNS):
                self.draw_tile(x, y, self.tile_state(y*self.TILES_COLUMNS+x))

        thumby.display.update()


    def draw_pick(self, frame):
        i = self.tiles[self.selected]
        x = self.scroll_x
        tile[i].x = -x

        thumby.display.fill(0)

        thumby.display.drawSprite(tile[i])

        correct = self.substate == self.PICKED_CORRECT
        if self.substate == self.PICKED_FIRST or correct:
            x = 44-x
            thumby.display.drawText(self.TILE_NAMES[i], x, 4, 1)
            thumby.display.drawText("Found!" if correct else "Find the same", x, 17, 1)
            thumby.display.drawText("Press action", x, 30, 1)
        elif self.substate == self.PICKED_WRONG:
            wrong.x = 40-x
            wrong.y = 12
            thumby.display.drawSprite(wrong)
            t = tile[self.tiles[self.picked]]
            t.x = 56-x
            thumby.display.drawSprite(t)

        thumby.display.update()


    def draw_win(self):
        thumby.display.fill(0)

        thumby.display.drawSprite(screen_game1)
        
        if self.substate == self.WIN_A:
            thumby.display.drawText("Player A wins!", 9, 28, 1)
        elif self.substate == self.WIN_B:
            thumby.display.drawText("Player B wins!", 9, 28, 1)
        else:
            thumby.display.drawText("Both players win!", 3, 28, 1)

        thumby.display.update()


    def process(self, frame):
        if self.state == self.STATE_START:
            self.draw_start()
            if thumby.buttonL.justPressed():
                self.substate = self.START_1
            elif thumby.buttonR.justPressed():
                self.substate = self.START_2
            elif thumby.actionJustPressed():
                self.players = 1 if self.substate == self.START_1 else 2
                self.state = self.STATE_PLAYING
        elif self.state == self.STATE_PLAYING:
            self.draw_tiles()
            if thumby.buttonL.justPressed():
                self.move(-1, 0)
            elif thumby.buttonU.justPressed():
                self.move(0, -1)
            elif thumby.buttonR.justPressed():
                self.move(+1, 0)
            elif thumby.buttonD.justPressed():
                self.move(0, +1)
            elif thumby.actionJustPressed():
                self.pick()
        elif self.state == self.STATE_PICKED:
            self.draw_pick(frame)
            if thumby.buttonL.pressed() or thumby.buttonL.justPressed(): # used also justPressed to reset just state
                self.scroll_x = max(self.scroll_x-1, 0)
            elif thumby.buttonR.pressed() or thumby.buttonR.justPressed(): # used also justPressed to reset just state
                self.scroll_x = min(self.scroll_x+1, 32)
            elif thumby.actionJustPressed():
                if self.players == 2 and self.substate == self.PICKED_WRONG:
                    self.player = 1 if self.player == 0 else 0
                if self.substate != self.PICKED_FIRST:
                    self.picked = -1
                if self.substate != self.PICKED_WRONG:
                    self.select_first_available()
                self.scroll_x = 0
                if not self.check_win():
                    self.state = self.STATE_PLAYING
        elif self.state == self.STATE_WIN:
            self.draw_win()
            if thumby.actionJustPressed():
                self.reset()
        return False


class Game2HUD:
    def __init__(self):
        self.health = 3         # number of hearts
        self.health_hurt = 0    # heart blinking, decreasing with each frate until zero
        self.health_width = 24
        self.health_height = 7
        self.health_x = thumby.display.width-self.health_width
        self.health_y = thumby.display.height-self.health_height


    def draw(self, frame):
        if self.health_hurt > 0:
            self.health_hurt -= 1

        thumby.display.drawFilledRectangle(self.health_x, self.health_y, self.health_width, self.health_height, 0)
        x = self.health_x+self.health_width
        for i in range(3):
            # empty or filled heart
            h = 1 if i < self.health else 0
            # heart blinking
            if i == self.health and self.health_hurt > 0 and frame&7 > 3:
                h = 1
            x -= 8
            heart[h].x = x
            heart[h].y = self.health_y
            thumby.display.drawSprite(heart[h])


    def reset(self):
        self.health = 3
        self.health_hurt = 0


    def take_damage(self):
        if self.health_hurt > 0:
            return
        self.health -= 1
        self.health_hurt = 32


class Game2:
    BROOM_MIN = -4
    BROOM_MAX = 20
    CRATE_STEP = 48
    CRATE_WIDTH = 16
    CRATE_CHECK_START = CRATE_STEP-CRATE_WIDTH
    CRATE_CHECK_STOP = CRATE_STEP
    FLOOR_EMPTY = 0
    FLOOR_CRATE_UP = 1
    FLOOR_CRATE_DOWN = 2
    FLOOR_CRATE_BETWEEN = 3
    STATE_START = 0
    STATE_PLAYING = 1
    STATE_PAUSED_CONTINUE = 2
    STATE_PAUSED_QUIT_GAME = 3
    STATE_WIN = 4
    STATE_GAME_OVER = 5


    def __init__(self):
        self.broom_y = 0         # vertical position
        self.broom_animation = 0 # frame 0-2
        self.floor = []
        self.floor_offset = 0
        self.hud = Game2HUD()
        self.state = self.STATE_START


    def animate_broom(self, frame):
        if frame&3 != 0:
            return

        self.broom_animation += 1
        if self.broom_animation > 2:
            self.broom_animation = 0


    def move_broom(self, delta_y):
        y = self.broom_y+delta_y

        if y < self.BROOM_MIN or y > self.BROOM_MAX:
            return

        self.broom_y = y
        broom[0].y = self.broom_y
        broom[1].y = self.broom_y+4
        broom[2].y = self.broom_y+8


    def move_bug(self):
        bug.x = 56-(self.floor_offset // 32)


    def start(self):
        thumby.display.setFont("/lib/font3x5.bin", 3, 5, 1)
        random.seed()

        self.broom_y = 8
        self.broom_animation = 0
        self.floor = [0, 0] + [random.randint(1, 3) for _ in range(32)]
        self.floor_offset = 0
        self.move_broom(0)
        self.hud.reset()
        self.state = self.STATE_START

        self.move_bug()
        bug.y = 16

        frame = 0
        while(1):
            frame += 1
            if self.process(frame):
                return


    def check_crate_collision(self):
        i = self.floor_offset % self.CRATE_STEP

        if i < self.CRATE_CHECK_START or i > self.CRATE_CHECK_STOP:
            return

        value = self.floor[self.floor_offset // self.CRATE_STEP+1]

        if value == self.FLOOR_EMPTY:
            return

        if value == self.FLOOR_CRATE_UP:
            if self.broom_y <= 8:
                self.hit_crate()
        elif value == self.FLOOR_CRATE_DOWN:
            if self.broom_y >= 8:
                self.hit_crate()
        else: # self.FLOOR_CRATE_BETWEEN
            if self.broom_y < 4 or self.broom_y >= 12:
                self.hit_crate()


    def hit_crate(self):
        self.hud.take_damage()
        if self.hud.health == 0:
            self.state = self.STATE_GAME_OVER


    def process(self, frame):
        if self.state == self.STATE_START:
            thumby.display.fill(0)
            thumby.display.drawSprite(screen_game2)
            thumby.display.drawText("Action to start", 7, 28, 1)
            thumby.display.update()
            if thumby.actionJustPressed():
                self.state = self.STATE_PLAYING
            return False

        if self.state == self.STATE_PAUSED_CONTINUE or self.state == self.STATE_PAUSED_QUIT_GAME:
            quit = self.state == self.STATE_PAUSED_QUIT_GAME
            thumby.display.fill(0)
            thumby.display.drawSprite(screen_game2)
            thumby.display.drawText("->", 10, 32 if quit else 24, 1)
            thumby.display.drawText("Continue", 20, 24, 1)
            thumby.display.drawText("Quit Game", 20, 32, 1)
            thumby.display.update()
            if quit:
                if thumby.buttonU.pressed():
                    self.state = self.STATE_PAUSED_CONTINUE
                elif thumby.actionJustPressed():
                    return True
            else:
                if thumby.buttonD.pressed():
                    self.state = self.STATE_PAUSED_QUIT_GAME
                elif thumby.actionJustPressed():
                    self.state = self.STATE_PLAYING
            return False

        if self.state == self.STATE_WIN:
            thumby.display.fill(0)
            thumby.display.drawSprite(screen_game2)
            thumby.display.drawText("YOU WIN!", 20, 28, 1)
            thumby.display.update()
            if thumby.actionJustPressed():
                self.start()
            return False

        if self.state == self.STATE_GAME_OVER:
            thumby.display.fill(0)
            thumby.display.drawSprite(screen_game2)
            thumby.display.drawText("GAME OVER", 18, 28, 1)
            thumby.display.update()
            if thumby.actionJustPressed():
                self.start()
            return False

        self.floor_offset += 1
        if self.floor_offset >= 1400: # bug is near to broom
            self.state = self.STATE_WIN
            return False

        self.animate_broom(frame)
        self.move_bug()
        self.check_crate_collision()

        thumby.display.fill(0)
        thumby.display.drawSprite(broom[self.broom_animation])
        thumby.display.drawSprite(bug)
        for i, value in enumerate(self.floor):
            if value == self.FLOOR_EMPTY:
                continue
            crate.x = (i*self.CRATE_STEP)-self.floor_offset
            if value == self.FLOOR_CRATE_UP:
                crate.y = 0
                thumby.display.drawSprite(crate)
            elif value == self.FLOOR_CRATE_DOWN:
                crate.y = 24
                thumby.display.drawSprite(crate)
            else: # self.FLOOR_CRATE_BETWEEN
                crate.y = -8
                thumby.display.drawSprite(crate)
                crate.y = 32
                thumby.display.drawSprite(crate)
        self.hud.draw(frame)
        thumby.display.update()

        if thumby.buttonU.pressed():
            self.move_broom(-1)
        elif thumby.buttonD.pressed():
            self.move_broom(+1)

        if thumby.actionJustPressed():
            self.state = self.STATE_PAUSED_CONTINUE

        return False


selected_game = 0
games = [
    Game1(),
    Game2(),
]
thumby.display.setFPS(24)
while(1):
    selected_game = select_game(selected_game)
    games[selected_game].start()
