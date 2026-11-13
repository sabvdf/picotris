from random import randint

x = 0
y = 0
addr_y = 0
addr_x = 0

width = 10
height = 20
field = [[0 for _ in range(width)] for _ in range(height)]

global score, level, total_lines, total_tetrises, next_level, step_time, new_brick_delay, paused
score = 0
total_lines = 0
total_tetrises = 0

while True:
    start = input("Start level (0-19, default 0): ")
    if start == "":
        start_level = 0
        break
    try:
        start_level = int(start)
        if 0 <= start_level <= 19:
            break
    except:
        pass

level = start_level
next_level = min(start_level * 10 + 10, max(100, (start_level * 10 - 50)))

step_time = 999
new_brick_delay = 0

paused = False
game_over = False

def toggle_pause():
    global paused
    paused = not paused
    update_paused(paused)

from constants import *

from console import *

update_score(score)

def change_level(new_level):
    global level, step_time
    level = new_level
    for l in GRAVITY:
        if l <= level:
            step_time = GRAVITY[l]
    update_level(level)

change_level(level)

def new_brick(previous):
    bricks = len(TETROMINOS)
    pick = randint(0, bricks)
    if pick == previous or pick == bricks:
        pick = randint(0, bricks-1)
    brick = TETROMINOS[pick]
    pivot = PIVOTS[pick]
    flip = FLIP[pick]
    return pick, brick, (width - len(brick[0])) // 2 + 1, 0, pivot, flip

global brick_type, current, bx, by, px, py, flip, flipped, blink
brick_type, current, bx, by, (px, py), flip = new_brick(-1)
flipped = False
blink = []

def rotate_brick(direction):
    bw = len(current[0])
    bh = len(current)

    counter = (flip and flipped) or (direction == -1 and not flip)

    rotated = []
    for _ in range(bw):
        rotated.append([0 for _ in range(bh)])

    for y in range(bw):
        for x in range(bh):
            if counter:
                rotated[y][x] = current[x][bw - y - 1]
            else:
                rotated[y][x] = current[bh - x - 1][y]

    new_px = py if counter else bh - py - 1
    new_py = bw - px - 1 if counter else px

    if bw == 2 and bh == 2:
        dx, dy = 0, 0
    else:
        dx, dy = px - new_px, py - new_py

    for y in range(bw):
        for x in range(bh):
            if rotated[y][x]:
                if (x + bx + dx >= FIELD_WIDTH or x + bx + dx < 0 or
                    y + by + dy >= FIELD_HEIGHT or y + by + dy < 0):
                    return False, current, (0, 0), (px, py), flipped
                
                if not(0 <= x + dx < bw and 0 <= y + dy < bh and current[y + dy][x + dx] != 0):
                    if get_pixel(x + bx + dx + FIELD_X, y + by + dy + FIELD_Y) != 0:
                        return False, current, (0, 0), (px, py), flipped

    return True, rotated, (dx, dy), (new_px, new_py), not flipped

def lower_brick(lines):
    max_y = 0
    h = len(current)
    w = len(current[0])

    while max_y < lines:
        for y in range(h):
            for x in range(w):
                if current[y][x]:
                    if ((y >= h-1 or (y < h-1 and current[y+1][x] == 0)) and
                        get_pixel(x + bx + FIELD_X, y + by + max_y + FIELD_Y + 1) != 0):
                        return max_y, True
        max_y += 1
        
    return max_y, False

def drop_brick(lines):
    global current, bx, by, px, py, flip, blink, new_brick_delay

    ny, blocked = lower_brick(lines)
    if not blocked:
        current, bx, by = update_brick(current, bx, by + ny)

    else:
        # Check lines
        h = len(current)
        full_lines = []
        for y in range(h):
            full = True
            for x in range(FIELD_WIDTH):
                if get_pixel(x + FIELD_X, y + by + FIELD_Y) == 0:
                    full = False
                    break
            if full:
                full_lines.append(y + by)

        scored = len(full_lines)
        if scored > 0:
            global score, next_level, total_lines, total_tetrises
            total_lines += scored
            score += LINES_SCORE[scored] * (level + 1)
            update_score(score)
            if scored == 4:
                total_tetrises += 1
                play_sfx("tetris")
            elif scored > 0:
                play_sfx("line")
            
            next_level -= scored
            if next_level <= 0:
                change_level(level + 1)
                next_level += 10
        
        for line in full_lines:
            blink.append(line)
            
        new_brick_delay = 11 + ((23 - by - h) // 4)
        current = []


def move_brick(dx):
    h = len(current)
    w = len(current[0])

    for y in range(h):
        for x in range(w):
            if current[y][x]:
                if ((x + dx >= w or x + dx < 0 or (0 <= x + dx < w and current[y][x+dx] == 0)) and
                    get_pixel(x + bx + dx + FIELD_X, y + by + FIELD_Y) != 0):
                    return 0
        
    return dx

def draw_brick(brick, bx, by, c):
    for y in range(len(brick)):
        for x in range(len(brick[y])):
            if brick[y][x]:
                if c == 0 or get_pixel(bx + x + FIELD_X, by + y + FIELD_Y) == 0:
                    set_pixel(bx + x + FIELD_X, by + y + FIELD_Y, c)
                else:
                    return False
    return True

draw_brick(current, bx, by, 1)

def update_brick(new_brick, new_bx, new_by):
    if len(current) > 0:
        draw_brick(current, bx, by, 0)
    if not draw_brick(new_brick, new_bx, new_by, 1):
        # Top out
        return [], 0, 0
    return new_brick, new_bx, new_by

brick_type, next_brick, next_bx, next_by, (next_px, next_py), next_flip = new_brick(brick_type)

timer = step_time
blink_step = 0

pressed = {Inputs.LEFT: False,
           Inputs.RIGHT: False,
           Inputs.ROTATE_L: False,
           Inputs.ROTATE_R: False,
           Inputs.DROP: False,
           Inputs.PAUSE: False}

DAS_L = -1
DAS_R = -1

while not game_over:
    try:
        while True:
            new_input = get_press()
            if new_input == Inputs.NONE:
                break
            if new_input == Inputs.EXIT:
                abort()
            if not pressed[new_input]:
                pressed[new_input] = True
                if new_input == Inputs.LEFT:
                    DAS_L = FIRST_DAS_DELAY + 1
                if new_input == Inputs.RIGHT:
                    DAS_R = FIRST_DAS_DELAY + 1
                elif new_input == Inputs.ROTATE_L:
                    if current != []:
                        rotated, brick, (dx, dy), (px, py), flipped = rotate_brick(-1)
                        if rotated:
                            current, bx, by = update_brick(brick, bx + dx, by + dy)
                elif new_input == Inputs.ROTATE_R:
                    if current != []:
                        rotated, brick, (dx, dy), (px, py), flipped = rotate_brick(1)
                        if rotated:
                            current, bx, by = update_brick(brick, bx + dx, by + dy)
                elif new_input == Inputs.DROP:
                    timer -= step_time - 2
                elif new_input == Inputs.PAUSE:
                    toggle_pause()

        while True:
            stop_input = get_release()
            if stop_input == Inputs.NONE:
                break
            pressed[stop_input] = False
        
        if current != []:
            if pressed[Inputs.LEFT]:
                DAS_L -= 1
                if DAS_L == 0 or DAS_L == FIRST_DAS_DELAY:
                    dx = move_brick(-1)
                    if dx != 0:
                        current, bx, by = update_brick(current, bx + dx, by)
                    if DAS_L == 0:
                        DAS_L = DAS_DELAY
            if pressed[Inputs.RIGHT]:
                DAS_R -= 1
                if DAS_R == 0 or DAS_R == FIRST_DAS_DELAY:
                    dx = move_brick(1)
                    if dx != 0:
                        current, bx, by = update_brick(current, bx + dx, by)
                    if DAS_R == 0:
                        DAS_R = DAS_DELAY
            
        if paused:
            sleep(TIME_STEP)
            continue

        timer -= 1

        if timer <= 0:

            if blink != []:
                if blink_step == FIELD_WIDTH+5:
                    last = blink.pop()
                    for y in range(last, 1, -1):
                        for x in range(FIELD_WIDTH):
                            set_pixel(x + FIELD_X, y + FIELD_Y, get_pixel(x + FIELD_X, y + FIELD_Y - 1))
                    for x in range(FIELD_WIDTH):
                        set_pixel(x + FIELD_X, 0, 0)

                    for b in range(len(blink)):
                        blink[b] = min(blink[b] + 1, 19)

                    if blink == []:
                        blink_step = 0

                else:
                    blink_step += 1
                    for line in blink:
                        for x in range(FIELD_WIDTH):
                            set_pixel(x + FIELD_X, line + FIELD_Y, 0 if blink_step in [x,FIELD_WIDTH+1,FIELD_WIDTH+3,FIELD_WIDTH+5] else 1)

                timer = BLINK_TIME
                    
            elif new_brick_delay > 0:
                new_brick_delay -= 1
                if new_brick_delay == 0:
                    draw_brick(next_brick, NEXT_BRICK_X, NEXT_BRICK_Y, 0)
                    
                    # New brick
                    current, bx, by = update_brick(next_brick, next_bx, next_by)
                    if current == []:
                        # Top out
                        game_over = True
                        
                        print(f"\n\nGAME OVER\nFinal score: {score}\nFinal level: {level}\nLines cleared: {total_lines}\nTetrises scored: {total_tetrises}")
                        abort()
                    else:
                        px, py, flip = next_px, next_py, next_flip
                        brick_type, next_brick, next_bx, next_by, (next_px, next_py), next_flip = new_brick(brick_type)
                        draw_brick(next_brick, NEXT_BRICK_X, NEXT_BRICK_Y, 1)

            else:
                # Move down
                drop_brick(1)

                timer = 2 if pressed[Inputs.DROP] else step_time
            
        update_display()
    except KeyboardInterrupt:
        abort()