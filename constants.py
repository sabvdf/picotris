from enum import Enum


SCREEN_WIDTH = 16
SCREEN_HEIGHT = 32

HALF_WIDTH = SCREEN_WIDTH // 2

MAX_X = SCREEN_WIDTH // 2 - 1
MAX_Y = SCREEN_HEIGHT - 1
MIN_Y2 = MAX_Y + 1
MAX_Y2 = SCREEN_HEIGHT * 2 - 1

FIELD_X = 1
FIELD_Y = 11
FIELD_WIDTH = 10
FIELD_HEIGHT = 20

NEXT_BRICK_X = 7 - FIELD_X
NEXT_BRICK_Y = 7 - FIELD_Y

TETROMINOS = [[[1,1,1,1]],
              [[1,1,1],[1,0,0]],
              [[1,1,1],[0,0,1]],
              [[1,1,1],[0,1,0]],
              [[1,1,0],[0,1,1]],
              [[0,1,1],[1,1,0]],
              [[1,1],[1,1]]]

PIVOTS = [(2,0),
          (1,0),
          (1,0),
          (1,0),
          (1,0),
          (1,0),
          (0,0)]

FLIP = [True,
        False,
        False,
        False,
        True,
        True,
        False]

BLINK_TIME = 1
TIME_STEP = 1.0 / 60.0

LINES_SCORE = [0, 40, 100, 300, 1200]

FIRST_DAS_DELAY = 16
DAS_DELAY = 6

GRAVITY = {
    0: 48,
    1: 43,
    2: 38,
    3: 33,
    4: 28,
    5: 23,
    6: 18,
    7: 13,
    8: 8,
    9: 6,
    10: 5,
    13: 4,
    16: 3,
    19: 2,
    29: 1
}

class Inputs(Enum):
    NONE = 0
    LEFT = 1
    RIGHT = 2
    ROTATE_L = 3
    ROTATE_R = 4
    DROP = 5
    PAUSE = 6
    EXIT = 7