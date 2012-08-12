SpaceAPI
========

SpaceAPI provides access to the k8055 USB interface board that is used to connect some of the Farset Labs facilities together, such as the 'Big Red Button', door striker, and door contact.

Access is provided via the SpaceAPIClient module, which exposes the following interfaces
* ```get(self,path, **params)```: Provides Raw access
* ```authGet(self,path, **params)``` : Provides Raw Authenticated Access, requires valid authpair=(username,password) to be passed at client init
* ```authPut(self,path, **params)``` : Ditto
* ```buttonDownState(self)``` : surprisingly enough, returns a bool of the button down state, i.e. True means the space should be open
* ```doorClosedState(self)``` : ditto, for the door
* ```spaceState(self)``` : Returns the current state of the space as defined in [The SpaceAPI](https://hackerspaces.nl/spaceapi/)
* ```openDoor(self)```: Guess what that does...
* ```set_open_state(self,state)```: sets the True/False open state of the space, i.e publically opens or closes the space.

##Example
>from SpaceAPIClient import client

>authpair=("username","TotallySecurePassword")

>base="http://farbot:5000"

>c=client(authpair=authpair,base=base)

>c.openDoor()

A Better, authenticationless example is ```doormonitor.py```

##Actual API Capabilities
* ```/space``` [GET] :returns the spaceAPI JSON (see spaceState())
* ```/space?state=<state in 'True','False'>``` [PUT, authenticated]: Set the space open state (will trigger irc/twitter from interaction with titania)

* ```/button``` [GET]: returns the 'pushed' state of the Big Red Button (True = 'The Space is open')
* ```/door``` [GET]: returns the closed state of the front door (True = Closed)
* ```/door/open``` [GET, authenticated]: unlocks the front door for about 5 seconds
* ```/board?type=<type in 'digital','analog'>&channel=<channel in [0-4] digital or [1-2] analog>``` [GET]: Read the board's inputs directly. If the type and channel are not defined, returns the digital inputs.


##Gotchas
* WSGI [strips](http://modwsgi.readthedocs.org/en/latest/configuration-directives/WSGIPassAuthorization.html) authentication information,so needs to be adjusted in the apache conf file 

