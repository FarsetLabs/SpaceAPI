from flask import Flask, Response, request
import atexit, signal
from functools import wraps
import k8055
import logging
from logging.handlers import TimedRotatingFileHandler, SysLogHandler
from gevent import killall

#Logging
handlers=[]
handlers.append(TimedRotatingFileHandler('/dev/shm/SpaceAPI.log',when='D',interval=1))
#handler = logging.FileHandler("/var/log/SpaceAPI.log")
handlers.append(SysLogHandler())
requests_logger = logging.getLogger('requests.packages.urllib3.connectionpool')
requests_logger.setLevel(logging.CRITICAL)

app = Flask(__name__)

#principals = Principal(app)

#open_state_permission = Permission(Need('open','space')))

for handler in handlers:
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
    ))
    app.logger.addHandler(handler)

app._board = k8055.Board()

app.logger.info("Set Up; loading views")
import SpaceAPI.views



