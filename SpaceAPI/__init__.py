from flask import Flask, Response, request
import atexit, signal
import logging as log
from functools import wraps
import k8055
import logging
from logging import StreamHandler
from gevent import killall
#handler = TimedRotatingFileHandler('/var/log/SpaceAPI.log',when='D',interval=1)
handler = logging.FileHandler("/var/log/SpaceAPI.log")
requests_logger = log.getLogger('requests.packages.urllib3.connectionpool')
requests_logger.setLevel(log.CRITICAL)

app = Flask(__name__)

handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
))
app.logger.addHandler(handler)

app._board = k8055.Board()
app.logger.info("Set Up; loading views")
import SpaceAPI.views



