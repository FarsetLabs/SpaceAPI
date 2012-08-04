#!/usr/bin/env python

from flask import Flask, url_for, Response, jsonify, request
from functools import wraps
import authdigest
import simplejson
import k8055
import logging as log
import time
from datetime import datetime as dt
import requests
from requests.auth import HTTPDigestAuth
urllib3_logger = log.getLogger('requests.packages.urllib3.connectionpool')
urllib3_logger.setLevel(log.CRITICAL)

import collections

log.basicConfig(level=log.DEBUG)

app = Flask(__name__)
                    

STRIKER_OP=1
STRIKER_TIME=2
JSON_FILE="/opt/SpaceAPI/farsetlabs.json"
BASE_URL = 'http://localhost:5000'
BIGREDINPUT = 4
BOARD_GETS={
    'digital':'digital_inputs',
    'analog':'analog'
}
BOARD_PUTS={
    'digital':'set_digital_output',
    'analog':'set_analog_output'
}
class FlaskRealmDigestDB(authdigest.RealmDigestDB):
    def requires_auth(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not self.isAuthenticated(request):
                return self.challenge()

            return f(*args, **kwargs)

        return decorated

authDB = FlaskRealmDigestDB('MyAuthRealm')
authDB.add_user('farbot', 'testing')

@app.route('/')
def api_root():
    return 'Welcome'

@app.route('/space', methods = ['GET'])
def api_space_status():
    content=simplejson.load(open(JSON_FILE,'r'))
    resp = jsonify(content)
    resp.status_code = 200
    return convert(resp)

@app.route('/door', methods = ['GET'])
@authDB.requires_auth
def api_open_door():
    resp = jsonify({'response':sesame()})
    resp.status_code = 200
    return resp

@app.route('/open', methods = ['PUT'])
@authDB.requires_auth
def api_open():
    error = None
    value = None
    status = 200
    try:
        json=simplejson.load(open(JSON_FILE,'r'))
        state = request.args.get('state', '')
        log.error(request)
        state = (state == "True")
        value = state
        json['open'] = state
        json['lastchange'] = dt.strftime(dt.utcnow(),"%s")
        json['status'] = "Open" if state else "Closed"
        simplejson.dump(json,
                        open(JSON_FILE,'w'),
                        indent=4,
                        sort_keys=True
                       )
    except Exception as err:
        error = "Error:%s"%err

    response = {
        'value':"%s"%value,
        'error':"%s"%error,
        'request':"%s"%request.args
    }
    log.debug(response)
    resp = jsonify(response)
    resp.status_code = status
    return resp



@app.route('/board', methods = ['GET','PUT'])
def api_board():
    error = "Failed"
    value = None
    status = 400
    if request.method == 'GET':
        try:
            type=request.args.get('type', '')
            channel=int(request.args.get('channel', ''))
            if type in BOARD_GETS.keys():
                ready_board()
                if type == 'digital':
                    value = app._board.digital_inputs[channel]
                    app._board.set_digital_output(channel,value)
                    error = None
                    status = 200
                elif type == 'analog':
                    getter = attrgetter(app._board,"analog%d"%channel)
                    value = getter
                    error = None
                    status = 200
                else:
                    error = "Invalid type and bad logic"
                    status = 500
            else:
                error = "Invalid type"
                status = 400
        except ValueError as err:
            error = "%s"%err
            status = 400
    elif authDB.isAuthenticated(request):
        # Client is authenticated
        value = "SuccessfulAuth"
        error = "PUT Not Implemented"
        status = 501
    else:
        return authDB.challenge()

    response = {
        'value':"%s"%value,
        'error':"%s"%error,
        'request':"%s"%request.args
    }
    log.debug(response)
    resp = jsonify(response)
    resp.status_code = status
    return resp

def convert(data):
    if isinstance(data, unicode):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data

def ready_board():
    try:
        app._board.read()
    except BoardError as Err:
        log.error("Lost Board: %s, restarting"%Err)
        app._board=k8055.Board()
        app._board.display_counter=2
        app._board.reset()
        ready_board()

def sesame(message=None):
    assert 0<=STRIKER_OP<=2, "Striker Output Out of Range"
    if message is not None:
        message = ": "+str(message)
    else:
        message = ""
    if STRIKER_OP > 0:
        log.info("Door unlocking%s"%(message))
        ready_board()
        try:
            set_analogue=getattr(app._board,"set_analog%d"%STRIKER_OP) #Temp Function
            set_analogue(255)
            log.info("Door unlocked")
            time.sleep(STRIKER_TIME)
            set_analogue(0)
            exit = "Door Successfully Unlocked and Relocked"
            log.info(exit)
        except Exception as E:
            exit="Door Problem: %s"%E
            log.info(exit)

    else:
        exit = "No Striker Configured, cannot continue"
        log.info(exit)
    return exit



if __name__ == '__main__':
    app._board = k8055.Board()
    app.run(host='0.0.0.0')

class AuthenticationException(Exception):
    pass

class client():

    def __init__(self,authpair=None,base=None):
        if authpair is not None:
            self.authpair=tuple(authpair)
        else:
            self.authpair=None
        if base is None:
            base = BASE_URL
        self.base = base

    def get(self, path, **params):
        path = "%s%s"%(self.base,path)
        return requests.get( path, params = params)

    def authGet(self, path, **params):
        path = "%s%s"%(self.base,path)
        if self.authpair is not None:
            return requests.get(path,auth=HTTPDigestAuth(*self.authpair))
        else:
            raise AuthenticationException

    def authPut(self, path, **params):
        path = "%s%s"%(self.base,path)
        if self.authpair is not None:
            return requests.put(path,auth=HTTPDigestAuth(*self.authpair), params=params)
        else:
            raise AuthenticationException

    def buttonState(self):
        r=self.get('/board',type='digital',channel=BIGREDINPUT)
        r=r.json
        if 'value' in r.keys():
            value = bool(r['value'])
        else:
            value = None
            raise ValueError("Button State Cannot Be Determined!%s"%r)
        return value

    def spaceState(self):
        r=self.get('/space')
        return r.json

    def set_open_state(self,open_state):
        return self.authPut('/open',state="%s"%open_state)



