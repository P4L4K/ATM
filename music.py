from pygame import mixer
import time

def play_sound(sound_file):
    mixer.init()
    mixer.music.load(sound_file)
    mixer.music.play()

    # Wait for the sound to finish playing
    while mixer.music.get_busy():
        time.sleep(1)

    mixer.quit()