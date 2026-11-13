def play_sfx(name):
    print(chr(27) + "[10;20H", end="")
    print(f"Audio: {name}")

def audio_game_over():
    play_sfx("gameover")