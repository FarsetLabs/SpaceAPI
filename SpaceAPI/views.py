from SpaceAPI import app
from SpaceAPI.auth import authDB
from SpaceAPI.settings import *
from datetime import datetime as dt
from flask import jsonify, request
from operator import attrgetter
import json

@app.route('/')
def api_root():
    return 'Welcome: Sorry that\'s an invalid API call. Go back to the <a href="https://github.com/FarsetLabs/SpaceAPI">docs</a>'

@app.route('/space', methods = ['GET'])
@app.route('/space/', methods = ['GET'])
def api_space_status():
    # Query for the SpaceAPI standard JSON response from the statefile
    content=json.load(open(JSON_FILE,'r'))
    resp = jsonify(content)
    resp.status_code = 200
    return convert(resp)

@app.route('/door', methods = ['GET'])
def api_door_closed_state():
    return digital_input_mask(DOORINPUT)

@app.route('/button', methods = ['GET'])
def api_button_down_state():
    return digital_input_mask(BIGREDINPUT)

@app.route('/door/open', methods = ['GET'])
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

@app.route('/space', methods = ['PUT'])
@authDB.requires_auth
def api_open():
    error = "Failed"
    value = None
    status = 400
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
        if len(request.args) == 2:
            ptype=request.args.get('type', '')
            channel=int(request.args.get('channel', ''))
            try:
                (value,status,error)=board_getter(ptype=ptype,channel=channel)

            except Exception as err:
                error = "Error in board response:%s"%err
                status = 400
        elif len(request.args) == 0:
            (value,status,error)=board_getter()
        else:
            value = None
            error = "Error in board request:%s"%request.args
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


