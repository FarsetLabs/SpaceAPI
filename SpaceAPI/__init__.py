from flask import Flask, Response, request
import logging as log
from functools import wraps
import k8055
import logging
from logging.handlers import SysLogHandler
log
requests_logger = log.getLogger('requests.packages.urllib3.connectionpool')
requests_logger.setLevel(log.CRITICAL)
app = Flask(__name__)
app._board = k8055.Board()

import SpaceAPI.views
