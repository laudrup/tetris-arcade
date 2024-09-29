"""
Tetris

Tetris clone, with some ideas from silvasur's code:
https://gist.github.com/silvasur/565419/d9de6a84e7da000797ac681976442073045c74a4

If Python and Arcade are installed, this example can be run from the command line with:
python -m arcade.examples.tetris
"""
import arcade
import random
import pathlib

# Set how many rows and columns we will have
ROW_COUNT = 25
COLUMN_COUNT = 10

# This sets the WIDTH and HEIGHT of each grid location
WIDTH = 40
HEIGHT = 40

# Do the math to figure out our screen dimensions
BOARD_WIDTH = WIDTH * COLUMN_COUNT
BOARD_HEIGHT = HEIGHT * ROW_COUNT
STATUS_WIDTH = 250
STATUS_HEIGHT = 200
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SCREEN_TITLE = "Tetris"
MENU_ENTRY_HEIGHT = 100
MENU_ENTRY_WIDTH = 500

PLAYER_1_KEYMAP = dict(
    UP=arcade.key.W,
    DOWN=arcade.key.S,
    LEFT=arcade.key.A,
    RIGHT=arcade.key.D
)

PLAYER_2_KEYMAP = dict(
    UP=arcade.key.UP,
    DOWN=arcade.key.DOWN,
    LEFT=arcade.key.LEFT,
    RIGHT=arcade.key.RIGHT
)

# Seconds before moving on key hold
KEY_REPEAT_SPEED = 0.45

colored_brick_files = [
    'transparent.png',
    'red.png',
    'green.png',
    'blue.png',
    'orange.png',
    'yellow.png',
    'purple.png',
    'cyan.png',
    'grey.png',
    'explosion.png'
]

# Define the shapes of the single parts
tetris_shapes = [
    [[1, 1, 1],
     [0, 1, 0]],

    [[0, 2, 2],
     [2, 2, 0]],

    [[3, 3, 0],
     [0, 3, 3]],

    [[4, 0, 0],
     [4, 4, 4]],

    [[0, 0, 5],
     [5, 5, 5]],

    [[6, 6, 6, 6]],

    [[7, 7],
     [7, 7]]
]

logo_grid = [
    [1, 1, 1, 1, 1, 0, 4, 4, 4, 0, 5, 5, 5, 5, 5, 0, 2, 2, 2, 0, 0, 3, 3, 3, 0, 0, 5, 5, 5],
    [0, 0, 1, 0, 0, 0, 4, 0, 0, 0, 0, 0, 5, 0, 0, 0, 2, 0, 0, 2, 0, 0, 3, 0, 0, 5, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 4, 4, 0, 0, 0, 0, 5, 0, 0, 0, 2, 2, 2, 0, 0, 0, 3, 0, 0, 0, 5, 5, 0],
    [0, 0, 1, 0, 0, 0, 4, 0, 0, 0, 0, 0, 5, 0, 0, 0, 2, 0, 2, 0, 0, 0, 3, 0, 0, 0, 0, 0, 5],
    [0, 0, 1, 0, 0, 0, 4, 4, 4, 0, 0, 0, 5, 0, 0, 0, 2, 0, 0, 2, 0, 3, 3, 3, 0, 5, 5, 5, 0]
]


def resource_path(fname):
    """Helper to load resources (images, sounds) from this files directory"""
    this_dir = pathlib.Path(__file__).parent.resolve()
    return this_dir / 'data' / fname


def create_textures():
    """ Create a list of images for sprites based on the global colors. """
    new_textures = []
    for brick_file in colored_brick_files:
        new_textures.append(arcade.load_texture(resource_path(brick_file)))
    return new_textures


texture_list = create_textures()


def setup_sprites(grid, left, height, bottom):
    sprite_list = arcade.SpriteList()
    for cy in range(len(grid)):
        for cx, cell in enumerate(grid[cy]):
            sprite = arcade.Sprite()
            for texture in texture_list:
                sprite.append_texture(texture)
                sprite.scale = float(WIDTH) / float(texture.width)
                sprite.center_x = (WIDTH * cx + WIDTH // 2) + left
                sprite.center_y = (height - HEIGHT * cy + HEIGHT // 2) + bottom
            if cell:
                sprite.set_texture(cell)
            sprite_list.append(sprite)
    return sprite_list


def rotate_counterclockwise(shape):
    return [[shape[y][x] for y in range(len(shape))]
            for x in range(len(shape[0]) - 1, -1, -1)]


def join_matrixes(matrix_1, matrix_2, matrix_2_offset):
    """ Copy matrix 2 onto matrix 1 based on the passed in x, y offset coordinate """
    offset_x, offset_y = matrix_2_offset
    for cy, row in enumerate(matrix_2):
        for cx, val in enumerate(row):
            matrix_1[cy + offset_y - 1][cx + offset_x] += val
    return matrix_1


class TetrisView(arcade.View):
    def __init__(self):
        super().__init__()
        self.background = arcade.load_texture(resource_path("bg.png"))

    def on_draw(self):
        arcade.draw_lrwh_rectangle_textured(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, self.background)

    def add_section(self, section):
        super().add_section(section)
        if hasattr(section, 'on_section_added'):
            section.on_section_added()


class MenuItem(arcade.Section):
    def __init__(self, left, bottom, width, height, title, handler):
        super().__init__(left, bottom, width, height, prevent_dispatch_view={False})
        self.title = title
        self.handler = handler
        self.background = arcade.load_texture(resource_path("menu_item_bg.png"))
        self.selected = False

    def on_draw(self):
        alpha = 255 if self.selected else 120
        arcade.draw_texture_rectangle(self.left + self.width / 2, self.bottom + self.height / 2, self.width, self.height, self.background, alpha=alpha)
        arcade.draw_text(self.title,
                         self.left,
                         self.bottom + 40,
                         arcade.color.WHITE,
                         20,
                         width=self.width,
                         align="center")


class MenuView(TetrisView):
    def __init__(self, entries):
        super().__init__()
        logo_height = len(logo_grid) * HEIGHT
        logo_width = len(logo_grid[0]) * WIDTH
        logo_left = (SCREEN_WIDTH - logo_width) / 2
        logo_bottom = SCREEN_HEIGHT - logo_height
        self.__sprite_list = setup_sprites(logo_grid, logo_left, logo_height, logo_bottom - 100)

        self.entries = []
        y_pos = logo_bottom - 250
        for title, func in entries:
            menu_item = MenuItem((SCREEN_WIDTH - MENU_ENTRY_WIDTH) / 2, y_pos, MENU_ENTRY_WIDTH, MENU_ENTRY_HEIGHT, title, func)
            self.add_section(menu_item)
            self.entries.append(menu_item)
            y_pos -= MENU_ENTRY_HEIGHT

        self.entries[0].selected = True

    def on_draw(self):
        super().on_draw()
        self.__sprite_list.draw()

    def on_key_press(self, key, _modifiers):
        idx, entry = [(i, e) for i, e in enumerate(self.entries) if e.selected][0]
        if key == arcade.key.UP and idx != 0:
            entry.selected = False
            self.entries[idx - 1].selected = True
        elif key == arcade.key.DOWN and idx != len(self.entries) - 1:
            entry.selected = False
            self.entries[idx + 1].selected = True
        elif key == arcade.key.ENTER:
            entry.handler()


class Tetromino():
    def __init__(self, board):
        self.board = board
        self.grid = random.choice(tetris_shapes)
        self.x = int(COLUMN_COUNT / 2 - self.width / 2)
        self.y = 0

    @property
    def height(self):
        return len(self.grid)

    @property
    def width(self):
        return len(self.grid[0])

    def move(self, delta_x):
        new_x = self.x + delta_x
        if new_x < 0:
            new_x = 0
        if new_x > COLUMN_COUNT - self.width:
            new_x = COLUMN_COUNT - self.width
        if not self.board.check_collision(self.grid, new_x, self.y):
            self.x = new_x

    def rotate(self):
        new_grid = rotate_counterclockwise(self.grid)
        new_width = len(new_grid[0])
        if self.x + new_width >= COLUMN_COUNT:
            self.x = COLUMN_COUNT - new_width
        if not self.board.check_collision(new_grid, self.x, self.y):
            self.grid = new_grid

    def draw(self):
        for row in range(len(self.grid)):
            for column in range(self.width):
                if self.grid[row][column]:
                    x = (WIDTH * (column + self.x) + WIDTH // 2)
                    y = (self.board.height - HEIGHT * (row + self.y) + HEIGHT // 2)
                    texture = texture_list[self.grid[row][column]]
                    sprite = arcade.Sprite(texture=texture)
                    sprite.scale = float(WIDTH) / float(sprite.width)
                    sprite.center_x = x + self.board.left
                    sprite.center_y = y + self.board.bottom
                    if sprite.center_y < self.board.top:
                        sprite.draw()


class BoardSection(arcade.Section):
    def __init__(self, left, bottom, width, height, **kwargs):
        super().__init__(left, bottom, width, height, prevent_dispatch={False}, prevent_dispatch_view={False}, **kwargs)
        self.rows_removed = 0
        self.__grid = [[0 for _x in range(COLUMN_COUNT)] for _y in range(ROW_COUNT + 1)]
        self.__sprite_list = setup_sprites(self.__grid, self.left, self.height, self.bottom)
        self.__rows_to_remove = []
        self.__garbage_to_add = 0
        self.__step = 0
        self.__explosion = arcade.Sound(':resources:sounds/explosion2.wav')
        self.__hit = arcade.Sound(':resources:sounds/hit5.wav')

    def remove_rows(self):
        for i, row in enumerate(self.__grid):
            if 0 not in row:
                self.__rows_to_remove.append(i)
        self.rows_removed = len(self.__rows_to_remove)

    def rows_to_remove(self):
        return len(self.__rows_to_remove) > 0

    def check_collision(self, grid, x, y):
        if y + len(grid) > len(self.__grid):
            self.__hit.play()
            return True
        for cy, row in enumerate(grid):
            for cx, cell in enumerate(row):
                if cell and self.__grid[cy + y][cx + x]:
                    self.__hit.play()
                    return True
        return False

    def add_stone(self, stone):
        self.__grid = join_matrixes(self.__grid, stone.grid, (stone.x, stone.y))

    def add_garbage(self, count):
        self.__garbage_to_add = count

    def removing_rows(self):
        return len(self.__rows_to_remove) == 0

    def on_update(self, dt):
        self.__step = 0 if self.__step == 10 else self.__step + 1

        for row in range(len(self.__grid)):
            for column in range(len(self.__grid[0])):
                v = self.__grid[row][column]
                i = row * COLUMN_COUNT + column
                if v == 0:
                    self.__sprite_list[i].visible = False
                else:
                    self.__sprite_list[i].visible = True
                    self.__sprite_list[i].set_texture(v)

        for i, row in enumerate(self.__rows_to_remove):
            if all(x == 0 for x in self.__grid[row]):
                del self.__grid[row]
                self.__grid.insert(0, [0 for _ in range(COLUMN_COUNT)])
                del self.__rows_to_remove[i]
                return
            for column in range(len(self.__grid[row])):
                if self.__grid[row][column] == 9:
                    self.__grid[row][column] = 0
                elif self.__grid[row][column] != 0:
                    self.__explosion.play()
                    self.__grid[row][column] = 9
                else:
                    continue
                return

        if self.__garbage_to_add > 0 and self.__step == 0:
            self.__grid.pop(0)
            garbage_column = [8 for _x in range(COLUMN_COUNT)]
            garbage_column[random.randint(0, COLUMN_COUNT - 1)] = 0
            self.__grid.append(garbage_column)
            self.__garbage_to_add -= 1
            self.__hit.play()

    def on_draw(self):
        for col in range(self.left, self.width + self.left + 1, WIDTH):
            arcade.draw_line(col, self.top, col, self.bottom, (*arcade.color.BYZANTINE, 50), 2)
        for row in range(self.bottom, self.height + self.bottom + 1, HEIGHT):
            arcade.draw_line(self.left, row, self.left + self.width, row, (*arcade.color.BYZANTINE, 50), 2)
        self.__sprite_list.draw()


class PlayerSection(arcade.Section):
    def __init__(self, left, bottom, width, height, keymap, **kwargs):
        super().__init__(left, bottom, width, height, prevent_dispatch={False}, prevent_dispatch_view={False}, **kwargs)
        self.keymap = keymap

        self.board_section = BoardSection(self.left + 5, self.bottom + 5, BOARD_WIDTH, BOARD_HEIGHT)
        self.level_section = InfoSection("Level", self.level, self.right + 20, self.bottom + height - STATUS_HEIGHT * 3)
        self.rows_remaining_section = InfoSection("Remaining", self.rows_remaining, self.right + 20, self.bottom + height - STATUS_HEIGHT * 2)
        self.next_stone_section = NextStoneSection(self.next_stone, self.right + 20, self.bottom + height - STATUS_HEIGHT)

        self.frame_count = 0
        self.game_over = False
        self.stone = None
        self.keys_pressed = {}

        self.__level = 1
        self.__rows_remaining = 10
        self.speed = 30
        self.__game_over_sound = arcade.Sound(':resources:sounds/gameover1.wav')
        self.__next_stone = Tetromino(self.board_section)
        self.new_stone()

        self.__incoming_garbage = 0

    def level(self):
        return self.__level

    def rows_remaining(self):
        return self.__rows_remaining

    def next_stone(self):
        return self.__next_stone

    def incoming_garbage(self, count=None):
        if count:
            self.__incoming_garbage += count
        return self.__incoming_garbage

    def new_stone(self):
        self.stone = self.__next_stone
        self.stone.y = 0
        self.stone.x = int(COLUMN_COUNT / 2 - self.stone.width / 2)
        self.__next_stone = Tetromino(self.board_section)
        if self.board_section.check_collision(self.stone.grid, self.stone.x, self.stone.y):
            self.__game_over_sound.play()
            self.game_over = True
        self.keys_pressed.clear()

    def drop(self):
        if not self.stone:
            return
        self.stone.y += 1
        if self.board_section.check_collision(self.stone.grid, self.stone.x, self.stone.y):
            self.board_section.add_stone(self.stone)
            if self.__incoming_garbage > 0:
                self.board_section.add_garbage(self.__incoming_garbage)
                self.__incoming_garbage = 0
            self.stone = None
            self.board_section.remove_rows()

    def rotate_stone(self):
        if not self.stone:
            return
        self.stone.rotate()

    def on_section_added(self):
        self.view.add_section(self.board_section)
        self.view.add_section(self.level_section)
        self.view.add_section(self.rows_remaining_section)
        self.view.add_section(self.next_stone_section)

    def on_update(self, dt):
        self.frame_count += 1
        for k in self.keys_pressed:
            self.keys_pressed[k] += dt
            if self.keys_pressed[k] > KEY_REPEAT_SPEED:
                if k == self.keymap["LEFT"]:
                    self.move(-1)
                if k == self.keymap["RIGHT"]:
                    self.move(1)
                if k == self.keymap["DOWN"]:
                    self.drop()
                self.keys_pressed[k] = 0.4
        if self.frame_count % self.speed == 0:
            self.drop()
        if not self.board_section.rows_to_remove() and not self.stone:
            if self.board_section.rows_removed > 0:
                self.view.on_rows_removed(self.board_section.rows_removed, self)
            self.__rows_remaining -= self.board_section.rows_removed
            if self.__rows_remaining <= 0:
                self.__level += 1
                self.__rows_remaining += 10
                self.speed -= 1
            self.new_stone()

    def move(self, delta_x):
        if not self.stone:
            return
        self.stone.move(delta_x)

    def on_key_press(self, key, modifiers):
        if key == self.keymap["UP"]:
            self.rotate_stone()
            return
        elif key == self.keymap["LEFT"]:
            self.move(-1)
        elif key == self.keymap["RIGHT"]:
            self.move(1)
        elif key == self.keymap["DOWN"]:
            self.drop()
        self.keys_pressed[key] = 0.0

    def on_key_release(self, key, modifiers):
        if key in self.keys_pressed:
            del self.keys_pressed[key]

    def on_draw(self):
        arcade.draw_lrtb_rectangle_outline(self.left, self.right, self.top, self.bottom, (*arcade.color.ANTIQUE_FUCHSIA, 100), 5)
        if self.stone:
            self.stone.draw()


class InfoSection(arcade.Section):
    def __init__(self, title, contents, left, bottom):
        super().__init__(left, bottom, STATUS_WIDTH, STATUS_HEIGHT, prevent_dispatch={False}, prevent_dispatch_view={False})
        self.title = title
        self.background = arcade.load_texture(resource_path("info_section_bg.png"))
        self.contents = contents

    def on_draw(self):
        arcade.draw_lrwh_rectangle_textured(self.left, self.bottom, self.width, self.height, self.background, alpha=100)
        arcade.draw_text(self.title,
                         self.left + 30,
                         self.bottom + self.height - 50,
                         arcade.color.WHITE,
                         20),

        arcade.draw_text(self.contents(),
                         self.left,
                         self.bottom + 55,
                         arcade.color.WHITE,
                         40,
                         width=self.width - 30,
                         align="right")


class NextStoneSection(arcade.Section):
    def __init__(self, stone, left, bottom, **kwargs):
        super().__init__(left, bottom, STATUS_WIDTH, STATUS_HEIGHT, prevent_dispatch={False}, prevent_dispatch_view={False}, **kwargs)
        self.background = arcade.load_texture(resource_path("info_section_bg.png"))
        self.stone = stone

    def on_draw(self):
        arcade.draw_lrwh_rectangle_textured(self.left, self.bottom, self.width, self.height, self.background, alpha=100)
        arcade.draw_text("Next",
                         self.left + 30,
                         self.bottom + self.height - 50,
                         arcade.color.WHITE,
                         20),
        stone = self.stone()
        stone.x = 12.4 if stone.width == 3 else (11.8 if stone.width == 4 else 12.7)
        stone.y = 2.9 if stone.height == 2 else 3.3
        stone.draw()


class GameOverSection(arcade.Section):
    def __init__(self):
        super().__init__(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, modal=True, enabled=False, prevent_dispatch_view={False})
        self.text = "Game Over!"

    def on_draw(self):
        start_x = 0
        start_y = SCREEN_HEIGHT / 2
        text = arcade.Text(self.text,
                           start_x,
                           start_y,
                           arcade.color.WHITE,
                           80,
                           width=SCREEN_WIDTH,
                           align="center",
                           bold=True)
        arcade.draw_lrtb_rectangle_filled(self.left, self.right, self.top, self.bottom, (128, 128, 128, 128))
        text.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.show_menu()


class SinglePlayerView(TetrisView):
    def __init__(self):
        super().__init__()
        self.__tetris = arcade.Sound(resource_path("tetris.wav"))
        self.__score = 0

        player_section_left = SCREEN_WIDTH // 2 - BOARD_WIDTH // 2 + 5
        player_section_bottom = SCREEN_HEIGHT // 2 - BOARD_HEIGHT // 2 + 5

        self.player_section = PlayerSection(player_section_left, player_section_bottom, BOARD_WIDTH + 10, BOARD_HEIGHT + 10, PLAYER_2_KEYMAP)
        self.add_section(self.player_section)

        self.score_section = InfoSection("Score", self.score, self.player_section.right + 20, player_section_bottom + BOARD_HEIGHT + 10 - STATUS_HEIGHT * 4)
        self.add_section(self.score_section)

        self.game_over_section = GameOverSection()
        self.add_section(self.game_over_section)

    @property
    def game_over(self):
        return self.player_section.game_over

    def score(self):
        return self.__score

    def on_rows_removed(self, rows_removed, player):
        if rows_removed == 1:
            self.__score += 100
        elif rows_removed == 2:
            self.__score += 150
        elif rows_removed == 3:
            self.__score += 400
        elif rows_removed == 4:
            self.__score += 1000
            self.__tetris.play()

    def on_update(self, dt):
        self.game_over_section.enabled = self.game_over

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.show_menu()


class TwoPlayerView(TetrisView):
    def __init__(self):
        super().__init__()
        self.__garbage = arcade.Sound(resource_path("garbage.wav"))

        player_one_section_left = SCREEN_WIDTH // 10 + 30
        player_two_section_left = player_one_section_left + BOARD_WIDTH * 2
        player_section_bottom = SCREEN_HEIGHT // 2 - BOARD_HEIGHT // 2 + 5

        self.player_one_section = PlayerSection(player_one_section_left, player_section_bottom, BOARD_WIDTH + 10, BOARD_HEIGHT + 10, PLAYER_1_KEYMAP)
        self.add_section(self.player_one_section)

        self.player_two_section = PlayerSection(player_two_section_left, player_section_bottom, BOARD_WIDTH + 10, BOARD_HEIGHT + 10, PLAYER_2_KEYMAP)
        self.add_section(self.player_two_section)

        self.player_one_incoming_section = InfoSection("Incoming", self.player_one_section.incoming_garbage, self.player_one_section.right + 20, self.player_one_section.bottom + BOARD_HEIGHT + 10 - STATUS_HEIGHT * 4)
        self.add_section(self.player_one_incoming_section)

        self.player_two_incoming_section = InfoSection("Incoming", self.player_two_section.incoming_garbage, self.player_two_section.right + 20, self.player_two_section.bottom + BOARD_HEIGHT + 10 - STATUS_HEIGHT * 4)
        self.add_section(self.player_two_incoming_section)

        self.game_over_section = GameOverSection()
        self.add_section(self.game_over_section)

    @property
    def game_over(self):
        return self.player_one_section.game_over or self.player_two_section.game_over

    def on_rows_removed(self, rows_removed, player):
        if rows_removed < 2:
            return
        self.__garbage.play()
        if player == self.player_one_section:
            self.player_two_section.incoming_garbage(rows_removed - 1)
        elif player == self.player_two_section:
            self.player_one_section.incoming_garbage(rows_removed - 1)

    def on_update(self, dt):
        if self.game_over:
            winning_player = "Player one" if self.player_two_section.game_over else "Player two"
            self.game_over_section.text = f"{winning_player} won!"
            self.game_over_section.enabled = True

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.show_menu()


class MainWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=True)
        self.theme_music = arcade.Sound(resource_path("korobeiniki.wav"), streaming=True)
        self.music_player = self.theme_music.play(loop=True)
        self.game_view = None
        self.show_menu()

    def show_menu(self):
        menu_entries = [] if not self.game_view or self.game_view.game_over else [
            ("Continue game", self.continue_game)
        ]
        menu_entries += [
            ("Singler player game", self.new_single_player_game),
            ("Two player game", self.new_two_player_game),
            ("Toggle fullscreen", self.toggle_fullscreen),
            ("Toggle music", self.toggle_music),
            ("Quit", arcade.exit)
        ]
        self.show_view(MenuView(menu_entries))

    def toggle_fullscreen(self):
        self.set_fullscreen(not self.fullscreen)

    def toggle_music(self):
        if self.theme_music.is_playing(self.music_player):
            self.music_player.pause()
        else:
            self.music_player.play()

    def continue_game(self):
        self.show_view(self.game_view)

    def new_single_player_game(self):
        self.game_view = SinglePlayerView()
        self.continue_game()

    def new_two_player_game(self):
        self.game_view = TwoPlayerView()
        self.continue_game()

    def on_resize(self, width, height):
        super().on_resize(width, height)
        width_ratio = width / SCREEN_WIDTH
        height_ratio = height / SCREEN_HEIGHT
        if height_ratio < width_ratio:
            new_width = width / height_ratio
            padding = (new_width - SCREEN_WIDTH) / 2
            self.set_viewport(-padding, new_width - padding, 0, SCREEN_HEIGHT)
        else:
            self.set_viewport(0, SCREEN_WIDTH, 0, height / width_ratio)


def main():
    window = MainWindow()
    window.run()


if __name__ == "__main__":
    main()
