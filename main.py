import time
import random
import logging
import threading
import urllib.parse


logging.basicConfig(level=logging.INFO)

from fastapi.responses import RedirectResponse
from gpiozero import MotionSensor
import uvicorn
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import vlc

logging.info("Initializing")

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

SOUND_IS_PLAYING = False

@app.get("/")
def index(request: Request, msg: str | None = None):
    sounds = list(quotes.keys())
    return templates.TemplateResponse(
        request=request, name="index.html", context={"sounds": sounds, "msg": msg}
    )

@app.get("/api/sound/{sound_name}")
def execute_sound(sound_name: str, background_tasks: BackgroundTasks):

    if SOUND_IS_PLAYING:
        message = urllib.parse.quote_plus("Sound failed, a sound is already in progress")
        return RedirectResponse(f"/?msg={message}")

    background_tasks.add_task(play_sound, sound_name)

    message = urllib.parse.quote_plus("Sound played successfully")
    return RedirectResponse(f"/?msg={message}")

# quote descriptor: (start time, length)
quotes = {
        "im_myrtle": (0, 23),
        "then_i_died": (31, 41),
        "throw_something_at_me": (82, 31),
        "long_time_no_see": (115, 25),
        "great_big_eyes": (140, 14),
        "the_other_boy": (160, 10),
        "thinking_about_death": (175, 7),
        "my_toilet": (237, 5),
}

def play_sound(sound: str):
    start_time, offset = quotes[sound]
    logging.info(f"Playing {sound} for {offset} seconds")

    global SOUND_IS_PLAYING 
    SOUND_IS_PLAYING = True

    player = vlc.MediaPlayer()
    player.audio_set_volume(220)

    media = vlc.Media(r"file:///home/myrtle-pi/myrtle.mp3")
    media.add_option(f"start-time={start_time}.0")

    player.set_media(media)
    
    player.play()

    time.sleep(offset)
    
    logging.info("Sound over")
    player.stop()

    SOUND_IS_PLAYING = False


def listen_for_motion():
    pir = MotionSensor(14)
     
    logging.info("Beginning pir sensor loop")
     
    while True:

        logging.info("Waiting for motion")
        pir.wait_for_motion()
        logging.info("Motion detected")

        desc = random.choice(list(quotes.keys()))

        if not SOUND_IS_PLAYING:
            play_sound(desc)
        else:
            logging.info(f"Failed to play sound {desc} as a sound is already in progress")


        logging.info("Waiting for no motion")
        pir.wait_for_no_motion()


if __name__ == "__main__":
    pir_t = threading.Thread(target=listen_for_motion)
    pir_t.start()

    uvicorn.run(app, host="0.0.0.0", port=8000)
    pir_t.join()

