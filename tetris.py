"""
Tetris

Tetris clone, with some ideas from silvasur's code:
https://gist.github.com/silvasur/565419/d9de6a84e7da000797ac681976442073045c74a4

If Python and Arcade are installed, this example can be run from the command line with:
python -m arcade.examples.tetris
"""
# flake8: noqa: E241
import arcade
import random
import pathlib

# Set how many rows and columns we will have
ROW_COUNT = 24
COLUMN_COUNT = 10

# This sets the WIDTH and HEIGHT of each grid location
WIDTH = 30
HEIGHT = 30

# Amount of frames between dropping stone down one row
SPEED = 10

# Do the math to figure out our screen dimensions
SCREEN_WIDTH = WIDTH * COLUMN_COUNT
SCREEN_HEIGHT = HEIGHT * ROW_COUNT
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
    'cyan.png'
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
    """ Rotates a matrix clockwise """
    return [[shape[y][x] for y in range(len(shape))]
            for x in range(len(shape[0]) - 1, -1, -1)]


def join_matrixes(matrix_1, matrix_2, matrix_2_offset):
    """ Copy matrix 2 onto matrix 1 based on the passed in x, y offset coordinate """
    offset_x, offset_y = matrix_2_offset
    for cy, row in enumerate(matrix_2):
        for cx, val in enumerate(row):
            matrix_1[cy + offset_y - 1][cx + offset_x] += val
    return matrix_1


class Board():
    def __init__(self):
        self.__grid = [[0 for _x in range(COLUMN_COUNT)] for _y in range(ROW_COUNT)]
        self.__grid += [[1 for _x in range(COLUMN_COUNT)]]
        self.__sprite_list = self.__setup_sprites()

    def __setup_sprites(self):
        sprite_list = arcade.SpriteList()
        for row in range(len(self.__grid)):
            for column in range(len(self.__grid[0])):
                sprite = arcade.Sprite()
                for texture in texture_list:
                    sprite.append_texture(texture)
                sprite.set_texture(0)
                sprite.scale = float(WIDTH) / float(sprite.width)
                sprite.center_x = WIDTH * column + WIDTH // 2
                sprite.center_y = SCREEN_HEIGHT - HEIGHT * row + HEIGHT // 2
                sprite_list.append(sprite)
        return sprite_list

    def remove_rows(self):
        while True:
            for i, row in enumerate(self.__grid[:-1]):
                if 0 not in row:
                    del self.__grid[i]
                    self.__grid.insert(0, [0 for _ in range(COLUMN_COUNT)])
                    break
            else:
                break

    def check_collision(self, shape, offset):
        """
        See if the matrix stored in the shape will intersect anything
        on the board based on the offset. Offset is an (x, y) coordinate.
        """
        off_x, off_y = offset
        for cy, row in enumerate(shape):
            for cx, cell in enumerate(row):
                if cell and self.__grid[cy + off_y][cx + off_x]:
                    return True
        return False

    def add_stone(self, stone, stone_x, stone_y):
        self.__grid = join_matrixes(self.__grid, stone, (stone_x, stone_y))

    def update(self):
        for row in range(len(self.__grid)):
            for column in range(len(self.__grid[0])):
                v = self.__grid[row][column]
                i = row * COLUMN_COUNT + column
                self.__sprite_list[i].set_texture(v)

    def draw(self):
        self.__sprite_list.draw()


class MyGame(arcade.Window):
    """ Main application class. """

    def __init__(self, width, height, title):
        """ Set up the application. """

        super().__init__(width, height, title, resizable=True)
        width, height = self.get_size()
        self.set_viewport(0, width, 0, height)

        arcade.set_background_color(arcade.color.WHITE)

        self.board = None
        self.frame_count = 0
        self.game_over = False
        self.paused = False

        self.stone = None
        self.stone_x = 0
        self.stone_y = 0

        self.keys_pressed = {}

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

    def new_stone(self):
        """
        Randomly grab a new stone and set the stone location to the top.
        If we immediately collide, then game-over.
        """
        self.stone = random.choice(tetris_shapes)
        self.stone_x = int(COLUMN_COUNT / 2 - len(self.stone[0]) / 2)
        self.stone_y = 0

        if self.board.check_collision(self.stone, (self.stone_x, self.stone_y)):
            self.game_over = True

    def setup(self):
        self.board = Board()
        self.new_stone()
        self.board.update()

    def drop(self):
        """
        Drop the stone down one place.
        Check for collision.
        If collided, then
          join matrixes
          Check for rows we can remove
          Update sprite list with stones
          Create a new stone
        """
        if not self.game_over and not self.paused:
            self.stone_y += 1
            if self.board.check_collision(self.stone, (self.stone_x, self.stone_y)):
                self.board.add_stone(self.stone, self.stone_x, self.stone_y)
                self.board.remove_rows()
                self.board.update()
                self.new_stone()

    def rotate_stone(self):
        """ Rotate the stone, check collision. """
        if not self.game_over and not self.paused:
            new_stone = rotate_counterclockwise(self.stone)
            if self.stone_x + len(new_stone[0]) >= COLUMN_COUNT:
                self.stone_x = COLUMN_COUNT - len(new_stone[0])
            if not self.board.check_collision(new_stone, (self.stone_x, self.stone_y)):
                self.stone = new_stone

    def on_update(self, dt):
        self.frame_count += 1
        if (arcade.key.LEFT, self.frame_count % KEY_REPEAT_SPEED) in self.keys_pressed.items():
            self.move(-1)
        if (arcade.key.RIGHT, self.frame_count % KEY_REPEAT_SPEED) in self.keys_pressed.items():
            self.move(1)
        if (arcade.key.DOWN, self.frame_count % KEY_REPEAT_SPEED) in self.keys_pressed.items():
            self.drop()
        if self.frame_count % SPEED == 0:
            self.drop()

    def move(self, delta_x):
        """ Move the stone back and forth based on delta x. """
        if not self.game_over and not self.paused:
            new_x = self.stone_x + delta_x
            if new_x < 0:
                new_x = 0
            if new_x > COLUMN_COUNT - len(self.stone[0]):
                new_x = COLUMN_COUNT - len(self.stone[0])
            if not self.board.check_collision(self.stone, (new_x, self.stone_y)):
                self.stone_x = new_x

    def on_key_press(self, key, modifiers):
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

    # noinspection PyMethodMayBeStatic
    def draw_grid(self, grid, offset_x, offset_y):
        """
        Draw the grid. Used to draw the falling stones. The board is drawn
        by the sprite list.
        """
        # Draw the grid
        for row in range(len(grid)):
            for column in range(len(grid[0])):
                # Figure out what color to draw the box
                if grid[row][column]:
                    # Do the math to figure out where the box is
                    x = WIDTH * (column + offset_x) +  WIDTH // 2
                    y = SCREEN_HEIGHT - HEIGHT * (row + offset_y) + HEIGHT // 2

                    # Draw the box
                    texture = texture_list[self.grid[row][column]]
                    sprite = arcade.Sprite(texture=texture)
                    sprite.scale = float(WIDTH) / float(sprite.width)
                    sprite.center_x = x
                    sprite.center_y = y
                    sprite.draw()

    def on_draw(self):
        """ Render the screen. """

        # This command has to happen before we start drawing
        self.clear()
        self.board.draw()
        self.draw_grid(self.stone, self.stone_x, self.stone_y)


def main():
    """ Create the game window, setup, run """
    my_game = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    my_game.setup()
    arcade.run()


if __name__ == "__main__":
    main()
