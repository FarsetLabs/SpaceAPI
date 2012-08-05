from SpaceAPI import app
from SpaceAPI.settings import *

@app.scheduler.task
def door_watcher():
    return digital_input_mask(DOORINPUT)
