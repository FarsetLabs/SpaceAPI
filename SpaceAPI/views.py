from SpaceAPI import app
from SpaceAPI.auth import authDB
from SpaceAPI.settings import *
from flask import jsonify, request
from datetime import datetime as dt
import time
import collections
from operator import attrgetter
import json


@app.route('/')
def api_root():
    return 'Welcome: Sorry that\'s an invalid API call. Go back to the docs'


@app.route('/space', methods = ['GET'])
def api_space_status():
    # Query for the SpaceAPI standard JSON response from the statefile
    content=json.load(open(JSON_FILE,'r'))
    resp = jsonify(content)
    resp.status_code = 200
    return convert(resp)

@app.route('/door', methods = ['GET'])
@authDB.requires_auth
def api_open_door():
    """
    Open the hackerspace doors hal...
    """
    (exit_msg,successfully_unlocked) = sesame()
    if successfully_unlocked:
        log=app.logger.info
    else:
        log=app.logger.error
    authdata=request.authorization
    source = request.remote_addr

    source_log(log,request,exit_msg)
    resp = jsonify({'response':exit_msg})
    resp.status_code = 200
    return resp

def sesame(message=None):
    """
    Internal Function to open/close the door
    """
    assert 0<=STRIKER_OP<=2, "Striker Output Out of Range"
    if message is not None:
        message = ": "+str(message)
    else:
        message = ""
    if STRIKER_OP > 0:
        ready_board()
        try:
            set_analogue=getattr(app._board,"set_analog%d"%STRIKER_OP) #Temp Function
            set_analogue(255)
            time.sleep(STRIKER_TIME)
            set_analogue(0)
            exit = ("Door Successfully Unlocked and Relocked",True)
        except Exception as E:
            exit=("Door Problem: %s"%E,False)
        finally:
            return exit
    else:
        exit = ("No Striker Configured, cannot continue",False)
    return exit

@app.route('/open', methods = ['PUT'])
@authDB.requires_auth
def api_open():
    error = None
    value = None
    status = 200
    try:
        config=json.load(open(JSON_FILE,'r'))
        state = request.args.get('state', '')
        app.logger.debug(request)
        state = (str(state) == "True") #Convert unicode true/false to bool
        value = state
        config['open'] = state
        config['lastchange'] = dt.strftime(dt.utcnow(),"%s")
        config['status'] = "Open" if state else "Closed"
        json.dump(
            config,
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

    app.logger.debug(response)
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
    app.logger.debug(response)
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
        app.logger.info("Board inputs:%s"%app._board.digital_inputs)
    except BoardError as Err:
        app.logger.error("Lost Board: %s, restarting"%Err)
        app._board=k8055.Board()
        app._board.display_counter=2
        app._board.reset()
        ready_board()

def source_log(logger, request, msg):
    """
    Lazy way to format the logs to any request responded to with auth/source info
    """
    log_text=str(msg)
    if hasattr(request,'authorization'):
        username = request.authorization.get('username')
        log_text+= " by %s"%username
    source = request.remote_addr
    log_text+= " from %s"%source
    logger(log_text)

