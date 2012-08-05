from flask import jsonify, request
from k8055 import BoardError, Board
import time
from SpaceAPI import app
import collections
import gevent
STRIKER_OP=1
STRIKER_TIME=2
JSON_FILE="/opt/SpaceAPI/farsetlabs.json"
BASE_URL = 'http://localhost:5000'
DOORINPUT = 3 #CUSTOM VALUE FOR FARSET LABS
BIGREDINPUT = 4 #CUSTOM VALUE FOR FARSET LABS
BOARD_GETS={
    'digital':'digital_inputs',
    'analog':'analog'
}
BOARD_PUTS={
    'digital':'set_digital_output',
    'analog':'set_analog_output'
}

def door_monitor(interval=1):
    doorclosed = app._board.digital_inputs[DOORINPUT]
    while True:
        ready_board()
        app.logger.info("Testing Door State")
        if app._board.digital_inputs[DOORINPUT] != doorclosed:
            doorclosed = app._board.digital_inputs[DOORINPUT]
            app.logger.info("Door %s"%("Closed" if doorclosed else "Opened"))
        gevent.sleep(interval)


def periodic_tasks(interval=1):
    return [ gevent.spawn(door_monitor) ]

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
        app.logger.debug("Board inputs:%s"%app._board.digital_inputs)
    except BoardError as Err:
        app.logger.error("Lost Board: %s, restarting"%Err)
        app._board=Board()
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

def board_getter(ptype=None,channel=None):
    error = "Failed from board_getter:%s,%s"%(ptype,channel)
    value = None
    status = 400
    if ptype in BOARD_GETS.keys():
        ready_board()
        if ptype == 'digital':
            ## Return the current value
            value = app._board.digital_inputs[channel]
            error = None
            status = 200
        elif ptype == 'analog':
            getter = attrgetter(app._board,"analog%d"%channel)
            value = getter()
            error = None
            status = 200
        else:
            error = "Invalid type and bad logic"
            status = 500
    else:
        error = "Invalid type"
        status = 400
    return (value,status,error)


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


def digital_input_mask(channel):
    error = "Failed"
    value = None
    status = 400

    try:
        ready_board()
        (value, status, error)= board_getter('digital',channel)
    except Exception as E:
        error = "%s"%E

    response = {
        'value':"%s"%value,
        'error':"%s"%error,
        'request':"%s"%request.args
    }

    app.logger.debug(response)
    resp = jsonify(response)
    resp.status_code = status
    return resp

