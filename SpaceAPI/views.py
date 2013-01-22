from SpaceAPI import app
from SpaceAPI.auth import authDB
from SpaceAPI.settings import *
from datetime import datetime as dt
from flask import jsonify, request
from flask.ext.login import (LoginManager, current_user, login_required,
                            login_user, logout_user, UserMixin, AnonymousUser,
                            confirm_login, fresh_login_required)
from operator import attrgetter
import json

@app.route('/')
def api_root():
    return 'Welcome: Sorry that\'s an invalid API call. Go back to the <a href="https://github.com/FarsetLabs/SpaceAPI">docs</a>'

# Login / out views
@app.route('/space/', methods = ['GET'])
@app.route('/space', methods = ['GET'])
def api_space_status():
    # Query for the SpaceAPI standard JSON response from the statefile
    content=json.load(open(JSON_FILE,'r'))
    resp = jsonify(content)
    resp.status_code = 200
    return convert(resp)


@app.route('/debug', methods = ['GET'])
@authDB.requires_admin
def api_space_debug():
    # Query for the SpaceAPI standard JSON response from the statefile
    content=json.load(open(JSON_FILE,'r'))
    resp = jsonify(content)
    resp.status_code = 200
    return convert(resp)

@app.route('/admin/adduser', methods = ['GET'])
@authDB.requires_admin
def api_add_user():
    error = "Failed"
    value = None
    status = 400
    try:
        username = request.args.get('username', '')
        password = request.args.get('password', '')
        if len(password) < 4:
            raise Exception("Password too short")

        app.logger.debug("Account requested for user %s with password length %d" % (username, len(password)))
        authDB.add_user(username, password)
        status=200
        error=None
    except Exception as err:
        error = "Error:%s"%err
	app.logger.error(error)

    response = {
        'value':"%s"%value,
        'error':"%s"%error,
        'request':"%s"%request.args
    }

    app.logger.debug(response)
    resp = jsonify(response)
    resp.status_code = status
    return resp



@app.route('/door', methods = ['GET'])
def api_door_closed_state():
    return digital_input_mask(DOORINPUT)

@app.route('/button', methods = ['GET'])
def api_button_open_state():
    return digital_input_mask(BIGREDINPUT)

@app.route('/door/open', methods = ['GET'])
@authDB.requires_auth
def api_open_door():
    """
    Open the hackerspace doors hal...
    """
    (exit_msg,successfully_unlocked) = sesame()
    source_log(app.logger.error,request,exit_msg)
    resp = jsonify({'response':exit_msg})
    resp.status_code = 200
    return resp

@app.route('/space/update', methods = ['PUT'])
@authDB.requires_auth
def api_open():
    error = "Failed"
    value = None
    status = 400
    try:
        config=json.load(open(JSON_FILE,'r'))
        state = request.args.get('state', None)
        if state is None:
	    state = digital_input_mask(BIGREDINPUT)
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
        status=200
        error=None
    except Exception as err:
        error = "Error:%s"%err
	app.logger.error(error)

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
		app.logger.error(error)
                status = 400
        elif len(request.args) == 0:
            (value,status,error)=board_getter()
        else:
            value = None
            error = "Error in board request:%s"%request.args
	    app.logger.error(error)
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


