from flask import Flask, Response, request
import atexit, signal
import logging as log
from functools import wraps
import k8055
import logging
from logging.handlers import TimedRotatingFileHandler
from gevent import killall
rotated_handler = TimedRotatingFileHandler('/var/log/SpaceAPI.log',when='D',interval=1)
requests_logger = log.getLogger('requests.packages.urllib3.connectionpool')
requests_logger.setLevel(log.CRITICAL)

def cleanup():
    print("Exiting")
    killall(app.periodic_tasks)

app = Flask(__name__)

if app.debug:
    rotated_handler.setLevel(logging.DEBUG)
    rotated_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
    ))
else:
    rotated_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
    ))
    rotated_handler.setLevel(logging.INFO)
app.logger.addHandler(rotated_handler)

#Have to import settings AFTER app instantiation
from SpaceAPI.settings import periodic_tasks
app.periodic_tasks=periodic_tasks(interval=1)

atexit.register(cleanup)
signal.signal(signal.SIGTERM, cleanup)

app._board = k8055.Board()
app.logger.info("Set Up; loading views")
import SpaceAPI.views



