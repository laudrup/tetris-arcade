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
ROW_COUNT = 24
COLUMN_COUNT = 10

# This sets the WIDTH and HEIGHT of each grid location
WIDTH = 40
HEIGHT = 40

# Amount of frames between dropping stone down one row
SPEED = 10

# Do the math to figure out our screen dimensions
BOARD_WIDTH = WIDTH * COLUMN_COUNT
BOARD_HEIGHT = HEIGHT * ROW_COUNT
STATUS_WIDTH = 120
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SCREEN_TITLE = "Tetris"

# Amount of frames between moving on key hold
KEY_REPEAT_SPEED = 7

colored_brick_files = [
    'transparent.png',
    'red.png',
    'green.png',
    'blue.png',
    'orange.png',
    'yellow.png',
    'purple.png',
    'cyan.png',
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


class Tetromino():
    def __init__(self, board):
        self.board = board
        self.grid = random.choice(tetris_shapes)
        self.x = int(COLUMN_COUNT / 2 - self.width / 2)
        self.y = 0

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


class Board(arcade.Section):
    def __init__(self, left, bottom, width, height, **kwargs):
        super().__init__(left, bottom, width, height, **kwargs)
        self.points_earned = 0
        self.__grid = [[0 for _x in range(COLUMN_COUNT)] for _y in range(ROW_COUNT)]
        self.__grid += [[1 for _x in range(COLUMN_COUNT)]]
        self.__sprite_list = self.__setup_sprites()
        self.__rows_to_remove = []
        self.__explosion = arcade.Sound(':resources:sounds/explosion2.wav')
        self.__hit = arcade.Sound(':resources:sounds/hit5.wav')

    def __setup_sprites(self):
        sprite_list = arcade.SpriteList()
        for row in range(len(self.__grid)):
            for column in range(len(self.__grid[0])):
                sprite = arcade.Sprite()
                for texture in texture_list:
                    sprite.append_texture(texture)
                sprite.set_texture(0)
                sprite.scale = float(WIDTH) / float(sprite.width)
                sprite.center_x = (WIDTH * column + WIDTH // 2) + self.left
                sprite.center_y = (self.height - HEIGHT * row + HEIGHT // 2) + self.bottom
                sprite_list.append(sprite)
        return sprite_list

    def remove_rows(self):
        for i, row in enumerate(self.__grid[:-1]):
            if 0 not in row:
                self.__rows_to_remove.append(i)
        if len(self.__rows_to_remove) == 1:
            self.points_earned = 20
        elif len(self.__rows_to_remove) == 2:
            self.points_earned = 50
        elif len(self.__rows_to_remove) == 3:
            self.points_earned = 120
        elif len(self.__rows_to_remove) == 4:
            self.points_earned = 300
        else:
            self.points_earned = 0

    def check_collision(self, grid, x, y):
        for cy, row in enumerate(grid):
            for cx, cell in enumerate(row):
                if cell and self.__grid[cy + y][cx + x]:
                    self.__hit.play()
                    return True
        return False

    def add_stone(self, stone):
        self.__grid = join_matrixes(self.__grid, stone.grid, (stone.x, stone.y))

    def update(self):
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
                return False
            for column in range(len(self.__grid[row])):
                if self.__grid[row][column] == 8:
                    self.__grid[row][column] = 0
                elif self.__grid[row][column] != 0:
                    self.__explosion.play()
                    self.__grid[row][column] = 8
                else:
                    continue
                return False

        return len(self.__rows_to_remove) == 0

    def draw(self):
        for col in range(self.left, self.width + self.left + 1, WIDTH):
            arcade.draw_line(col, self.top, col, self.bottom, (*arcade.color.BYZANTINE, 50), 2)
        for row in range(self.bottom, self.height + self.bottom + 1, HEIGHT):
            arcade.draw_line(self.left, row, self.left + self.width, row, (*arcade.color.BYZANTINE, 50), 2)
        self.__sprite_list.draw()


class PlayerSection(arcade.Section):
    def __init__(self, left, bottom, width, height, **kwargs):
        super().__init__(left, bottom, width, height, **kwargs)
        self.board = Board(self.left + 5, self.bottom + 5, BOARD_WIDTH, BOARD_HEIGHT)
        self.frame_count = 0
        self.game_over = False
        self.stone = None
        self.keys_pressed = {}
        self.points = 0
        self.__game_over_sound = arcade.Sound(':resources:sounds/gameover1.wav')
        self.new_stone()

    def new_stone(self):
        self.stone = Tetromino(self.board)
        if self.board.check_collision(self.stone.grid, self.stone.x, self.stone.y):
            self.__game_over_sound.play()
            self.game_over = True

    def draw_game_over(self):
        start_x = self.left
        start_y = SCREEN_HEIGHT / 2
        arcade.draw_text("GAME OVER",
                         start_x,
                         start_y,
                         arcade.color.BARBIE_PINK,
                         40,
                         width=BOARD_WIDTH,
                         align="center",
                         bold=True)

    def drop(self):
        if not self.stone:
            return
        self.stone.y += 1
        if self.board.check_collision(self.stone.grid, self.stone.x, self.stone.y):
            self.board.add_stone(self.stone)
            self.stone = None
            self.board.remove_rows()

    def rotate_stone(self):
        if not self.stone:
            return
        self.stone.rotate()

    def update(self, dt):
        if self.game_over:
            return
        self.frame_count += 1
        if (arcade.key.LEFT, self.frame_count % KEY_REPEAT_SPEED) in self.keys_pressed.items():
            self.move(-1)
        if (arcade.key.RIGHT, self.frame_count % KEY_REPEAT_SPEED) in self.keys_pressed.items():
            self.move(1)
        if (arcade.key.DOWN, self.frame_count % KEY_REPEAT_SPEED) in self.keys_pressed.items():
            self.drop()
        if self.frame_count % SPEED == 0:
            self.drop()
        if self.board.update() and not self.stone:
            self.points += self.board.points_earned
            self.new_stone()

    def move(self, delta_x):
        if not self.stone:
            return
        self.stone.move(delta_x)

    def on_key_press(self, key, modifiers):
        if self.game_over:
            return
        if key == arcade.key.UP:
            self.rotate_stone()
            return
        elif key == arcade.key.LEFT:
            self.move(-1)
        elif key == arcade.key.RIGHT:
            self.move(1)
        elif key == arcade.key.DOWN:
            self.drop()
        self.keys_pressed[key] = self.frame_count % KEY_REPEAT_SPEED

    def on_key_release(self, key, modifiers):
        if key in self.keys_pressed:
            del self.keys_pressed[key]

    def on_draw(self):
        arcade.draw_lrtb_rectangle_outline(self.left, self.right, self.top, self.bottom, (*arcade.color.ANTIQUE_FUCHSIA, 100), 5)
        self.board.draw()
        if self.stone:
            self.stone.draw()
        if self.game_over:
            self.draw_game_over()


class ScoreSection(arcade.Section):
    def __init__(self, left, bottom, width, height, **kwargs):
        super().__init__(left, bottom, width, height, **kwargs)

    @property
    def score(self):
        return self.view.player_section.points

    def on_draw(self):
        arcade.draw_lrtb_rectangle_filled(self.left, self.right, self.bottom + 90, self.bottom, (*arcade.color.AFRICAN_VIOLET, 25))
        arcade.draw_line(self.left, self.bottom + 50, self.right, self.bottom + 50, (*arcade.color.BOYSENBERRY, 150), 3)
        arcade.draw_text("Score",
                         self.left + 5,
                         self.bottom + 60,
                         (*arcade.color.BABY_BLUE, 200),
                         20),

        arcade.draw_text(self.score,
                         self.left,
                         self.bottom + 15,
                         (*arcade.color.BABY_BLUE, 200),
                         20,
                         width=self.width - 10,
                         align="right")


class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        self.background = arcade.load_texture(resource_path("bg.png"))

        player_section_left = SCREEN_WIDTH // 2 - BOARD_WIDTH // 2 + 5
        player_section_bottom = SCREEN_HEIGHT // 2 - BOARD_HEIGHT // 2 + 5
        self.player_section = PlayerSection(player_section_left, player_section_bottom, BOARD_WIDTH + 10, BOARD_HEIGHT + 10, prevent_dispatch_view={False})
        self.score_section = ScoreSection(self.player_section.right + 20, player_section_bottom, STATUS_WIDTH, 100, prevent_dispatch_view={False})
        self.add_section(self.player_section)
        self.add_section(self.score_section)

    def on_draw(self):
        arcade.start_render()
        arcade.draw_lrwh_rectangle_textured(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, self.background)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.F:
            self.window.set_fullscreen(not self.window.fullscreen)
        elif key == arcade.key.Q:
            arcade.exit()


class MainWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=True)
        self.game_view = GameView()
        self.show_view(self.game_view)

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
